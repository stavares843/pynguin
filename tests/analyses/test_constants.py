#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2022 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
import pytest

from pynguin.analyses.constants import (
    ConstantPool,
    DynamicConstantProvider,
    EmptyConstantProvider,
    RestrictedConstantPool,
)


@pytest.fixture()
def pool() -> ConstantPool:
    return ConstantPool()


@pytest.fixture()
def rpool() -> ConstantPool:
    return RestrictedConstantPool(max_size=5)


def test_has_constant(pool):
    pool.add_constant(42)
    assert pool.has_constant_for(int)


def test_has_no_constant(pool):
    assert not pool.has_constant_for(int)


def test_get_constant_for(pool):
    pool.add_constant(42)
    assert pool.get_constant_for(int) == 42


def test_add_constant(pool):
    pool.add_constant(42)
    assert pool._constants[int] == {42}


def test_remove_constant(pool):
    pool.add_constant(42)
    pool.add_constant(17)
    assert len(pool) == 2
    pool.remove_constant(17)
    assert len(pool) == 1


def test_get_all_constants(pool):
    pool.add_constant(42)
    pool.add_constant(5)
    assert pool.get_all_constants_for(int) == {5, 42}


def test_len(pool):
    assert len(pool) == 0


def test_len_not_empty(pool):
    pool.add_constant(42)
    pool.add_constant(13.37)
    assert len(pool) == 2


def test_restriced(rpool):
    for i in range(20):
        rpool.add_constant(i)
    assert rpool.get_all_constants_for(int) == {15, 16, 17, 18, 19}


def test_restriced_str(rpool):
    for i in range(20):
        rpool.add_constant(chr(ord("A") + i))
    assert rpool.get_all_constants_for(str) == {"P", "Q", "R", "S", "T"}


def test_dynamic_constant_pool_max_size(rpool):
    provider = DynamicConstantProvider(rpool, EmptyConstantProvider(), 0, 5)
    provider.add_value("abcd")
    provider.add_value("abcde")
    provider.add_value("abcdef")
    assert rpool.get_all_constants_for(str) == {"abcd", "abcde"}
