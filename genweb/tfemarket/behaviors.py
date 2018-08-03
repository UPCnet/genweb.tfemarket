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
from plone.registry.interfaces import IRegistry

from genweb.tfemarket import _
from genweb.tfemarket.z3cwidget import FieldsetFieldWidget

import datetime


def expiresDefaultValue():
    return dt_end_of_day(datetime.datetime.today() + datetime.timedelta(365))


class IPublicationOffer(model.Schema):

    form.widget('fieldset_opt', FieldsetFieldWidget)
    fieldset_opt = schema.Text(
        default=_(u'Dates'),
        required=False,
    )

    effective = schema.Datetime(
        title=_PMF(u'label_effective_date', u'Publishing Date'),
        description=_(
            u'help_effective_date',
            default=u"The date the item will be published."),
        required=True
    )

    expired= schema.Datetime(
        title=_PMF(u'label_expiration_date', u'Expiration Date'),
        description=_(
            u'help_expiration_date',
            default=u"The date that the item will expire."),
        required=False,
        defaultFactory=expiresDefaultValue,
    )

    form.omitted('effective', 'expired')
    form.no_omit(IEditForm, 'effective', 'expired')
    form.no_omit(IAddForm, 'effective', 'expired')


alsoProvides(IPublicationOffer, IFormFieldProvider)


class PublicationOffer(MetadataBase):
    effective = DCFieldProperty(
        IPublicationOffer['effective'],
        get_name='effective_date'
    )
    expired = DCFieldProperty(
        IPublicationOffer['expired'],
        get_name='expiration_date'
    )
