# -*- coding: utf-8 -*-

from five import grok
from plone import api
from plone.directives import dexterity
from plone.directives import form
from zope import schema

from genweb.tfemarket import _
from genweb.tfemarket.utils import checkPermissionCreateApplications
from genweb.tfemarket.z3cwidget import ReadOnlyInputFieldWidget
from genweb.tfemarket.z3cwidget import StudentInputFieldWidget


grok.templatedir("templates")


class IApplication(form.Schema):
    """ Application for an offer
    """

    form.widget('offer_id', ReadOnlyInputFieldWidget)
    offer_id = schema.TextLine(
        title=_(u'Offer id'),
        required=True,
    )

    form.widget('offer_title', ReadOnlyInputFieldWidget)
    offer_title = schema.TextLine(
        title=_(u'Offer title'),
        required=True,
    )

    form.widget('dni', ReadOnlyInputFieldWidget)
    dni = schema.TextLine(
        title=_(u'DNI'),
        required=True,
    )

    form.widget('title', StudentInputFieldWidget)
    title = schema.TextLine(
        title=_(u'Fullname'),
        required=True,
    )

    phone = schema.TextLine(
        title=_(u"Telephone"),
        required=False,
    )

    form.widget('email', ReadOnlyInputFieldWidget)
    email = schema.TextLine(
        title=_(u'Email'),
        required=True,
    )

    form.mode(prisma_id='hidden')
    prisma_id = schema.TextLine(
        title=_(u'PRISMA id'),
        required=False,
    )

    form.mode(llista_expedients='hidden')
    llista_expedients = schema.List(
        title=_(u'Llista Expedients'),
        value_type=schema.TextLine(),
        required=False,
    )

    body = schema.Text(
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
    grok.require('zope2.View')
    grok.context(IApplication)
    grok.template('application_view')

    def redirectToMarket(self):
        roles = api.user.get_current().getRoles()
        market_path = self.context.getParentNode().getParentNode().absolute_url()
        if 'Manager' in roles or 'Market Manager' in roles:
            self.redirect(market_path + "?offer=" + self.context.offer_id + "&open=Y")
        else:
            self.redirect(market_path)
