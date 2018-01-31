# -*- coding: utf-8 -*-

from plone.directives import form
from zope import schema

from genweb.tfemarket import _


class IMarket(form.Schema):
    """ Folder that contains all request to a TFE
    """

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Description'),
        required=False,
    )
