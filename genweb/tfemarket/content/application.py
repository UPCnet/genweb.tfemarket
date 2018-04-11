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
        default=u'',
    )

    directives.mode(offer_title="display")
    offer_title = schema.TextLine(
        title=_(u'Offer title'),
        required=False,
        default=u'',
    )

    primary('dni')
    directives.mode(dni="display")
    dni = schema.TextLine(
        title=_(u'DNI'),
        required=False,
        default=u'',
    )

    directives.mode(fullname="display")
    fullname = schema.TextLine(
        title=_(u'Fullname'),
        required=False,
        default=u'',
    )

    directives.mode(email="display")
    email = schema.TextLine(
        title=_(u'Email'),
        required=False,
        default=u'',
    )

    phone = schema.TextLine(
        title=_(u"Telephone"),
        required=False,
        default=u'',
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

        self.fields['offer_id'].field.default = self.context.offer_id
        self.fields['offer_title'].field.default = self.context.title

        current = api.user.get_current()
        user = getLdapExactUserData(current.id)
        if user:
            self.fields['dni'].field.default = user['DNIpassport']
            self.fields['fullname'].field.default = user['sn']
            self.fields['email'].field.default = user['mail']
            if user.has_key('telephoneNumber'):
                self.fields['phone'].field.default = user['telephoneNumber']


class View(grok.View):
    grok.context(IApplication)
    grok.template('application_view')
