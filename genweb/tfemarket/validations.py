# -*- coding: utf-8 -*-

from Products.CMFDefault.exceptions import EmailAddressInvalid
from Products.CMFDefault.utils import checkEmailAddress
from zope.schema import ValidationError


class InvalidEmailAddress(ValidationError):
    "Invalid email address"


def validateEmail(value):
    try:
        checkEmailAddress(value)
    except EmailAddressInvalid:
        raise InvalidEmailAddress(value)
    return True
