# -*- coding: utf-8 -*-

from five import grok
from plone import api
from plone.app.textfield import RichText as RichTextField
from plone.autoform import directives
from plone.directives import form, dexterity
from plone.supermodel.directives import primary
from zope import schema

from genweb.tfemarket import _
from genweb.tfemarket.utils import checkPermissionCreateApplications
from genweb.tfemarket.utils import getLdapExactUserData
from genweb.tfemarket.validations import validateEmail

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
        required=False,
    )

    directives.mode(title="display")
    title = schema.TextLine(
        title=_(u'Fullname'),
        required=False,
    )

    directives.mode(dni="display")
    dni = schema.TextLine(
        title=_(u'DNI'),
        required=False,
    )

    directives.mode(email="display")
    email = schema.TextLine(
        title=_(u'Email'),
        required=False,
    )

    phone = schema.TextLine(
        title=_(u"Telephone"),
        required=False,
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
            self.context.plone_utils.addPortalMessage(_(u"You have already created an application. You can see it on the main page of the market."), 'error')
            self.redirect(self.context.absolute_url())


class View(grok.View):
    grok.context(IApplication)
    grok.template('application_view')
