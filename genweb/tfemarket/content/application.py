# -*- coding: utf-8 -*-

from plone.directives import form, dexterity
from five import grok
from plone.autoform import directives
from zope import schema
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from plone.app.textfield import RichText as RichTextField

from genweb.tfemarket import _
from genweb.tfemarket.utils import checkPermissionCreateApplications

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

        if not checkPermissionCreateApplications(self, self.context):
            self.context.plone_utils.addPortalMessage(_(u"You have already created an application."), 'error')
            self.redirect(self.context.absolute_url())


class View(grok.View):
    grok.context(IApplication)
    grok.template('application_view')
