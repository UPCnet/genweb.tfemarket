from Products.CMFDefault.utils import checkEmailAddress
from Products.CMFDefault.exceptions import EmailAddressInvalid
from zope.schema import ValidationError

from genweb.tfemarket import _


class InvalidEmailAddress(ValidationError):
    "Invalid email address"


def validateEmail(value):
    try:
        checkEmailAddress(value)
    except EmailAddressInvalid:
        raise InvalidEmailAddress(value)
    return True
