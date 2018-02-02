# -*- coding: utf-8 -*-

from zope import schema
from z3c.form import button
from plone.supermodel import model
from plone.app.registry.browser import controlpanel
from Products.statusmessages.interfaces import IStatusMessage

from genweb.tfemarket import _


class ITfemarketSettings(model.Schema):
    """ Global TFE Market settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    model.fieldset(
        'Settings',
        _(u'Settings'),
        fields=['review_state'],
    )

    model.fieldset(
        'TopicTFE',
        _(u'Topics'),
        fields=['topics'],
    )

    model.fieldset(
        'TFE Tags',
        _(u'Tags'),
        fields=['tags'],
    )

    model.fieldset(
        'Temes',
        _(u'Temes'),
        fields=['field3'],
    )

    review_state = schema.Bool(title=_(u"Review State"),
                               default=False,
                               description=_(u'Select if you want to add "Reviewer" role'),
                               required=False,
                               )

    topics = schema.TextLine(
        title=_(u"Topics of the TFE"),
        required=False,
    )

    tags = schema.TextLine(
        title=_(u"URL del servei web"),
        required=False,
    )

    field3 = schema.TextLine(
        title=_(u"URL del servei web"),
        required=False,
    )


class TfemarketSettingsEditForm(controlpanel.RegistryEditForm):

    schema = ITfemarketSettings
    label = _(u'UPC Mercat TFE')


class TfemarketSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = TfemarketSettingsEditForm
