#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

def key_suffix(value):
    """Возвращает суффикс для типа ключа."""
    mapping = {
        'RSA': '-rsa',
        'ECDSA': '-ecdsa',
        'ED25519': '-ed25519'
    }
    return mapping.get(value.upper(), '-unknown')


class FilterModule(object):
    def filters(self):
        return {
            'key_suffix': key_suffix
        }