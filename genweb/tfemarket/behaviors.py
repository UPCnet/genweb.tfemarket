from DateTime import DateTime
from z3c.form.interfaces import IEditForm, IAddForm
from zope.interface import provider
from zope.interface import alsoProvides
from zope import schema
from plone.autoform import directives as form
from plone.app.dexterity.behaviors.metadata import DCFieldProperty
from plone.app.dexterity.behaviors.metadata import MetadataBase
from plone.supermodel import model
from plone.autoform.interfaces import IFormFieldProvider
from plone.app.dexterity import PloneMessageFactory as _PMF


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
        required=True
    )

    expires = schema.Datetime(
        title=_PMF(u'label_expiration_date', u'Expiration Date'),
        description=_PMF(
            u'help_expiration_date',
            default=u"When this date is reached, the content will no"
                    u"longer be visible in listings and searches."),
        required=True
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
