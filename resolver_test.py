import pytest

import logging

import resolver

import socket

logger = logging.getLogger("resolver")
logger.setLevel(logging.ERROR)

BASIC = [
    "yandex.ru",
    "pikabu.ru",
    "ads.adfox.ru"
]

ALIAS = [
    "matchid.adfox.yandex.ru",
    "banners.adfox.ru"
]


def validate(trace_record: resolver.TraceRecord):
    try:
        socket.inet_aton(trace_record.response.address)
    except Exception:
        return False
    return True


@pytest.mark.parametrize("target", BASIC)
def test_resolve_basic(target):
    assert validate(resolver.resolve(target)[-1])


@pytest.mark.parametrize("target", ALIAS)
def test_resolve_alias(target):
    assert validate(resolver.resolve(target)[-1])


@pytest.mark.parametrize("target", BASIC)
def test_resolve_no_cache(target):
    first_resolve = resolver.resolve(target, need_trace=True)
    second_resolve = resolver.resolve(target, need_trace=True)
    assert len(first_resolve) == len(second_resolve)


@pytest.mark.parametrize("target", BASIC)
def test_resolve_use_cache(target):
    first_resolve = resolver.resolve(target, need_trace=True)
    second_resolve = resolver.resolve(target, need_trace=False)
    assert len(second_resolve) == 1
    assert len(first_resolve) != 1
