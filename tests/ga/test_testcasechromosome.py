#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2021 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
from unittest import mock
from unittest.mock import MagicMock, call

import pytest

import pynguin.configuration as config
import pynguin.ga.testcasechromosome as tcc
import pynguin.testcase.defaulttestcase as dtc
import pynguin.testcase.statements.parametrizedstatements as ps
import pynguin.testcase.statements.primitivestatements as prim
import pynguin.testcase.testfactory as tf
from pynguin.testcase.execution.executionresult import ExecutionResult


@pytest.fixture
def test_case_chromosome():
    return tcc.TestCaseChromosome(dtc.DefaultTestCase())


@pytest.fixture
def test_case_chromosome_with_test():
    test_case = dtc.DefaultTestCase()
    return tcc.TestCaseChromosome(test_case), test_case


def test_has_changed_default(test_case_chromosome):
    assert test_case_chromosome.has_changed()


@pytest.mark.parametrize("value", [pytest.param(True), pytest.param(False)])
def test_has_changed(test_case_chromosome, value):
    test_case_chromosome.set_changed(value)
    assert test_case_chromosome.has_changed() == value


def test_get_last_execution_last_result_default(test_case_chromosome):
    assert test_case_chromosome.get_last_execution_result() is None


def test_set_last_execution_result(test_case_chromosome):
    result = MagicMock(ExecutionResult)
    test_case_chromosome.set_last_execution_result(result)
    assert test_case_chromosome.get_last_execution_result() == result


def test_get_last_mutatable_statement_empty(test_case_chromosome):
    assert test_case_chromosome.get_last_mutatable_statement() is None


def test_get_last_mutatable_statement_max(test_case_chromosome_with_test):
    chromosome, test_case = test_case_chromosome_with_test
    test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    assert chromosome.get_last_mutatable_statement() == 0


def test_get_last_mutatable_statement_mid(test_case_chromosome_with_test):
    chromosome, test_case = test_case_chromosome_with_test
    test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    result = MagicMock(ExecutionResult)
    result.has_test_exceptions.return_value = True
    result.get_first_position_of_thrown_exception.return_value = 1
    chromosome.set_last_execution_result(result)
    assert chromosome.get_last_mutatable_statement() == 1


def test_get_last_mutatable_statement_too_large(test_case_chromosome_with_test):
    chromosome, test_case = test_case_chromosome_with_test
    test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    result = MagicMock(ExecutionResult)
    result.has_test_exceptions.return_value = True
    result.get_first_position_of_thrown_exception.return_value = 4
    chromosome.set_last_execution_result(result)
    assert chromosome.get_last_mutatable_statement() == chromosome.size() - 1


def test_mutation_insert_none(test_case_chromosome):
    config.configuration.search_algorithm.statement_insertion_probability = 0.0
    assert not test_case_chromosome._mutation_insert()


def test_mutation_insert_two():
    test_factory = MagicMock(tf.TestFactory)

    def side_effect(tc, pos):
        tc.add_statement(prim.IntPrimitiveStatement(tc, 5))
        return 0

    test_factory.insert_random_statement.side_effect = side_effect
    test_case = dtc.DefaultTestCase()
    chromosome = tcc.TestCaseChromosome(test_case, test_factory=test_factory)
    config.configuration.search_algorithm.statement_insertion_probability = 0.5
    config.configuration.search_algorithm.chromosome_length = 10
    with mock.patch("pynguin.utils.randomness.next_float") as float_mock:
        float_mock.side_effect = [0.2, 0.2, 0.2]
        assert chromosome._mutation_insert()
    test_factory.insert_random_statement.assert_has_calls(
        [call(test_case, 0), call(test_case, 1)]
    )


def test_mutation_insert_twice_no_success():
    test_factory = MagicMock(tf.TestFactory)

    def side_effect(tc, pos):
        return -1

    test_factory.insert_random_statement.side_effect = side_effect
    test_case = dtc.DefaultTestCase()
    chromosome = tcc.TestCaseChromosome(test_case, test_factory=test_factory)
    config.configuration.search_algorithm.statement_insertion_probability = 0.5
    config.configuration.search_algorithm.chromosome_length = 10
    with mock.patch("pynguin.utils.randomness.next_float") as float_mock:
        float_mock.side_effect = [0.2, 0.2, 0.2]
        assert not chromosome._mutation_insert()
    test_factory.insert_random_statement.assert_has_calls(
        [call(test_case, 0), call(test_case, 0)]
    )


def test_mutation_insert_max_length():
    test_factory = MagicMock(tf.TestFactory)

    def side_effect(tc, pos):
        tc.add_statement(prim.IntPrimitiveStatement(tc, 5))
        return 0

    test_factory.insert_random_statement.side_effect = side_effect
    test_case = dtc.DefaultTestCase()
    chromosome = tcc.TestCaseChromosome(test_case, test_factory=test_factory)
    config.configuration.search_algorithm.statement_insertion_probability = 0.5
    config.configuration.search_algorithm.chromosome_length = 1
    with mock.patch("pynguin.utils.randomness.next_float") as float_mock:
        float_mock.side_effect = [0.0, 0.0]
        assert chromosome._mutation_insert()
    test_factory.insert_random_statement.assert_has_calls([call(test_case, 0)])
    assert test_case.size() == 1


def test_mutation_change_nothing_to_change(test_case_chromosome):
    assert not test_case_chromosome._mutation_change()


def test_mutation_change_single_prim(test_case_chromosome_with_test):
    chromosome, test_case = test_case_chromosome_with_test
    int0 = prim.IntPrimitiveStatement(test_case, 5)
    int0.ret_val.distance = 5
    test_case.add_statement(int0)
    with mock.patch("pynguin.utils.randomness.next_float") as float_mock:
        float_mock.return_value = 0.0
        assert chromosome._mutation_change()
        assert int0.ret_val.distance == 5


@pytest.mark.parametrize("result", [pytest.param(True), pytest.param(False)])
def test_mutation_change_call_success(constructor_mock, result):
    factory = MagicMock(tf.TestFactory)
    factory.change_random_call.return_value = result
    test_case = dtc.DefaultTestCase()
    chromosome = tcc.TestCaseChromosome(test_case, test_factory=factory)
    const0 = ps.ConstructorStatement(test_case, constructor_mock)
    const0.ret_val.distance = 5
    test_case.add_statement(const0)
    with mock.patch("pynguin.utils.randomness.next_float") as float_mock:
        float_mock.return_value = 0.0
        with mock.patch.object(const0, "mutate") as mutate_mock:
            mutate_mock.return_value = False
            assert chromosome._mutation_change() == result
            mutate_mock.assert_called_once()
            assert const0.ret_val.distance == 5


def test_mutation_change_no_change(test_case_chromosome_with_test):
    chromosome, test_case = test_case_chromosome_with_test
    test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    with mock.patch("pynguin.utils.randomness.next_float") as float_mock:
        float_mock.return_value = 1.0
        assert not chromosome._mutation_change()


@pytest.mark.parametrize("result", [pytest.param(True), pytest.param(False)])
def test_delete_statement(result):
    test_factory = MagicMock(tf.TestFactory)
    test_factory.delete_statement_gracefully.return_value = result
    test_case = dtc.DefaultTestCase()
    chromosome = tcc.TestCaseChromosome(test_case, test_factory=test_factory)
    test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    assert chromosome._delete_statement(0) == result
    test_factory.delete_statement_gracefully.assert_called_with(test_case, 0)


def test_mutation_delete_empty(test_case_chromosome):
    assert not test_case_chromosome._mutation_delete()


def test_mutation_delete_not_empty():
    test_case = dtc.DefaultTestCase()
    chromosome = tcc.TestCaseChromosome(test_case)
    int0 = prim.IntPrimitiveStatement(test_case, 5)
    int1 = prim.IntPrimitiveStatement(test_case, 5)
    test_case.add_statement(int0)
    test_case.add_statement(int1)
    with mock.patch("pynguin.utils.randomness.next_float") as float_mock:
        float_mock.side_effect = [0.0, 1.0]
        with mock.patch.object(chromosome, "_delete_statement") as delete_mock:
            delete_mock.return_value = True
            assert chromosome._mutation_delete()
            delete_mock.assert_has_calls([call(1)])
            assert delete_mock.call_count == 1


def test_mutation_delete_skipping():
    test_case = dtc.DefaultTestCase()
    chromosome = tcc.TestCaseChromosome(test_case)
    with mock.patch.object(chromosome, "_delete_statement") as delete_mock:
        delete_mock.return_value = True
        with mock.patch.object(chromosome, "get_last_mutatable_statement") as mut_mock:
            mut_mock.return_value = 3
            assert not chromosome._mutation_delete()
            assert delete_mock.call_count == 0


def test_mutate_chop(test_case_chromosome_with_test):
    chromosome, test_case = test_case_chromosome_with_test
    chromosome.set_changed(False)
    for i in range(50):
        test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    config.configuration.search_algorithm.test_insert_probability = 0.0
    config.configuration.search_algorithm.test_change_probability = 0.0
    config.configuration.search_algorithm.test_delete_probability = 0.0
    with mock.patch.object(chromosome, "get_last_mutatable_statement") as mut_mock:
        mut_mock.return_value = 5
        with mock.patch.object(chromosome, "_test_factory") as factory_mock:
            factory_mock.has_call_on_sut.return_value = True
            chromosome.mutate()
            assert chromosome.has_changed()
            assert len(test_case.statements) == 6
            assert factory_mock.has_call_on_sut.call_count == 1


def test_mutate_no_chop(test_case_chromosome_with_test):
    chromosome, test_case = test_case_chromosome_with_test
    for i in range(50):
        test_case.add_statement(prim.IntPrimitiveStatement(test_case, 5))
    chromosome.set_changed(False)
    config.configuration.search_algorithm.test_insert_probability = 0.0
    config.configuration.search_algorithm.test_change_probability = 0.0
    config.configuration.search_algorithm.test_delete_probability = 0.0
    with mock.patch.object(chromosome, "get_last_mutatable_statement") as mut_mock:
        mut_mock.return_value = None
        with mock.patch.object(chromosome, "_test_factory") as factory_mock:
            factory_mock.has_call_on_sut.return_value = True
            chromosome.mutate()
            assert len(test_case.statements) == 50
            assert not chromosome.has_changed()
            assert factory_mock.has_call_on_sut.call_count == 1


@pytest.mark.parametrize(
    "func,rand,result",
    [
        pytest.param("_mutation_delete", [0, 1, 1], True),
        pytest.param("_mutation_delete", [0, 1, 1], False),
        pytest.param("_mutation_change", [1, 0, 1], True),
        pytest.param("_mutation_change", [1, 0, 1], False),
        pytest.param("_mutation_insert", [1, 1, 0], True),
        pytest.param("_mutation_insert", [1, 1, 0], False),
    ],
)
def test_mutate_all(test_case_chromosome, func, rand, result):
    test_case_chromosome.set_changed(False)
    with mock.patch("pynguin.utils.randomness.next_float") as float_mock:
        float_mock.side_effect = rand
        with mock.patch.object(test_case_chromosome, func) as mock_func:
            mock_func.return_value = result
            with mock.patch.object(
                test_case_chromosome, "_test_factory"
            ) as factory_mock:
                factory_mock.has_call_on_sut.return_value = True
                test_case_chromosome.mutate()
                assert test_case_chromosome.has_changed() == result
                mock_func.assert_called_once()


def test_crossover_wrong_type(test_case_chromosome):
    with pytest.raises(AssertionError):
        test_case_chromosome.cross_over(MagicMock(), 0, 0)


def test_crossover_success():
    test_factory = MagicMock()
    test_case0 = MagicMock(dtc.DefaultTestCase)
    test_case0_clone = MagicMock(dtc.DefaultTestCase)
    test_case0_clone.size.return_value = 5
    test_case0.clone.return_value = test_case0_clone
    test_case1 = MagicMock(dtc.DefaultTestCase)
    test_case1.size.return_value = 7
    left = tcc.TestCaseChromosome(test_case0, test_factory=test_factory)
    right = tcc.TestCaseChromosome(test_case1, test_factory=test_factory)

    left.cross_over(right, 4, 3)
    assert test_case1.get_statement.call_count == 4
    assert test_factory.append_statement.call_count == 4


def test_crossover_too_large():
    test_factory = MagicMock()
    test_case0 = MagicMock(dtc.DefaultTestCase)
    test_case0_clone = MagicMock(dtc.DefaultTestCase)
    test_case0_clone.size.return_value = 5
    test_case0.clone.return_value = test_case0_clone
    test_case1 = MagicMock(dtc.DefaultTestCase)
    test_case1.size.return_value = 7
    left = tcc.TestCaseChromosome(test_case0, test_factory=test_factory)
    right = tcc.TestCaseChromosome(test_case1, test_factory=test_factory)
    config.configuration.search_algorithm.chromosome_length = 3
    left.set_changed(False)
    left.cross_over(right, 1, 2)
    assert not left.has_changed()


def test_is_failing(test_case_chromosome):
    chromosome = test_case_chromosome
    result = MagicMock(ExecutionResult)
    result.has_test_exceptions.return_value = True
    chromosome.set_last_execution_result(result)
    assert chromosome.is_failing()


def test_is_failing_without_execution_result(test_case_chromosome):
    chromosome = test_case_chromosome
    assert not chromosome.is_failing()


def test_accept(test_case_chromosome):
    visitor = MagicMock()
    test_case_chromosome.accept(visitor)
    visitor.visit_test_case_chromosome.assert_called_once_with(test_case_chromosome)


def test_invalidate_fitness_cache(test_case_chromosome):
    fitness = MagicMock()
    fitness.is_maximisation_function.return_value = False
    test_case_chromosome.add_fitness_function(fitness)
    test_case_chromosome._update_fitness_values(fitness, MagicMock())
    assert test_case_chromosome.fitness_values != {}
    test_case_chromosome.invalidate_fitness_values()
    assert test_case_chromosome.fitness_values == {}
