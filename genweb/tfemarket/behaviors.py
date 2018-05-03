# -*- coding: utf-8 -*-

from plone.app.dexterity import PloneMessageFactory as _PMF
from plone.app.dexterity.behaviors.metadata import DCFieldProperty
from plone.app.dexterity.behaviors.metadata import MetadataBase
from plone.app.event.base import dt_end_of_day
from plone.app.event.base import dt_start_of_day
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from zope import schema
from zope.interface import alsoProvides

import datetime


def effectiveDefaultValue():
    return dt_start_of_day(datetime.datetime.today() + datetime.timedelta(1))


def expiresDefaultValue():
    return dt_end_of_day(datetime.datetime.today() + datetime.timedelta(365))


class IPublicationOffer(model.Schema):

    model.fieldset(
        'dates',
        label=_PMF(u'label_schema_dates', default=u'Dates'),
        fields=['effective', 'expires'],
    )

    effective = schema.Datetime(
        title=_PMF(u'label_effective_date', u'Publishing Date'),
        description=_PMF(
            u'help_effective_date',
            default=u"If this date is in the future, the content will "
                    u"not show up in listings and searches until this date."),
        required=True,
        defaultFactory=effectiveDefaultValue,
    )

    expires = schema.Datetime(
        title=_PMF(u'label_expiration_date', u'Expiration Date'),
        description=_PMF(
            u'help_expiration_date',
            default=u"When this date is reached, the content will no"
                    u"longer be visible in listings and searches."),
        required=True,
        defaultFactory=expiresDefaultValue,
    )

    form.omitted('effective', 'expires')
    form.no_omit(IEditForm, 'effective', 'expires')
    form.no_omit(IAddForm, 'effective', 'expires')


alsoProvides(IPublicationOffer, IFormFieldProvider)


class PublicationOffer(MetadataBase):
    effective = DCFieldProperty(
        IPublicationOffer['effective'],
        get_name='effective_date'
    )
    expires = DCFieldProperty(
        IPublicationOffer['expires'],
        get_name='expiration_date'
    )
