import logging
import socket

import pytest

import resolver

logger = logging.getLogger("resolver")
logger.setLevel(logging.ERROR)

BASIC = [
    ("yandex.ru", None),
    ("pikabu.ru", None),
    ("ads.adfox.ru", "77.88.21.179")
]

ALIAS = [
    ("matchid.adfox.yandex.ru", "93.158.134.118"),
    ("banners.adfox.ru", "93.158.134.158")
]

INVALID = [
    "yandex.xxx.uuuu",
    "best.hhh.ddddd"
    "123456"
]


def validate(trace_record: resolver.TraceRecord):
    try:
        socket.inet_aton(trace_record.response.address)
    except Exception:
        return False
    return True


@pytest.mark.parametrize("target,expected", BASIC)
def test_resolve_basic(target, expected):
    result = resolver.resolve(target)[-1]
    assert validate(result)
    if expected:
        assert result.response.address == expected


@pytest.mark.parametrize("target,expected", BASIC)
def test_resolve_basic_repeat(target, expected):
    for _ in range(10):
        result = resolver.resolve(target)[-1]
        assert validate(result)
        if expected:
            assert result.response.address == expected


@pytest.mark.parametrize("target", INVALID)
def test_resolve_invalid(target):
    result = resolver.resolve(target)[-1]
    assert result.response.address is None


@pytest.mark.parametrize("target", INVALID)
def test_resolve_invalid_repeat(target):
    for _ in range(10):
        result = resolver.resolve(target)[-1]
        assert result.response.address is None


@pytest.mark.parametrize("target,expected", ALIAS)
def test_resolve_alias(target, expected):
    result = resolver.resolve(target)[-1]
    assert validate(result)
    if expected:
        assert result.response.address == expected


@pytest.mark.parametrize("target,expected", BASIC)
def test_resolve_no_cache(target, expected):
    first_resolve = resolver.resolve(target, need_trace=True)
    second_resolve = resolver.resolve(target, need_trace=True)
    assert len(first_resolve) == len(second_resolve)


@pytest.mark.parametrize("target,expected", BASIC)
def test_resolve_use_cache(target, expected):
    first_resolve = resolver.resolve(target, need_trace=True)
    second_resolve = resolver.resolve(target, need_trace=False)
    assert len(second_resolve) == 1
    assert len(first_resolve) != 1
