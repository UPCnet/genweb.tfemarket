# -*- coding: utf-8 -*-

from plone.directives import form, dexterity
from five import grok
from plone.autoform import directives
from zope import schema
from plone.app.textfield import RichText as RichTextField
from genweb.tfemarket import _

grok.templatedir("templates")


class IApplication(form.Schema):
    """ Application for an offer
    """

    directives.mode(offer_id="display")
    offer_id = schema.TextLine(
        title=_(u'Offer id'),
        required=False,
    )

    directives.mode(offer_title="display")
    offer_title = schema.TextLine(
        title=_(u'Offer title'),
        required=True,
    )

    dni = schema.TextLine(
        title=_(u'Identification number'),
        required=True,
    )

    title = schema.TextLine(
        title=_(u'Name and surname'),
        required=True,
    )

    body = RichTextField(
        title=_(u'Body'),
        required=False,
    )


class Add(dexterity.AddForm):

    grok.name('application')

    def updateWidgets(self):
        super(Add, self).updateWidgets()

        self.widgets["dni"].value = 'lalalala'
