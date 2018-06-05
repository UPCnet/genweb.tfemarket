# -*- coding: utf-8 -*-

from five import grok
from plone.app.textfield import RichText as RichTextField
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
        required=False,
    )

    form.widget('offer_title', ReadOnlyInputFieldWidget)
    offer_title = schema.TextLine(
        title=_(u'Offer title'),
        required=False,
    )

    form.widget('title', StudentInputFieldWidget)
    title = schema.TextLine(
        title=_(u'Fullname'),
        required=False,
    )

    form.widget('dni', ReadOnlyInputFieldWidget)
    dni = schema.TextLine(
        title=_(u'DNI'),
        required=False,
    )

    form.widget('email', ReadOnlyInputFieldWidget)
    email = schema.TextLine(
        title=_(u'Email'),
        required=False,
    )

    phone = schema.TextLine(
        title=_(u"Telephone"),
        required=False,
    )

    form.widget('prisma_id', ReadOnlyInputFieldWidget)
    prisma_id = schema.TextLine(
        title=_(u'PRISMA id'),
        required=False,
    )

    llista_expedients = schema.List(
        title=_(u'Llista Expedients'),
        value_type=schema.TextLine(),
        required=False,
    )

    body = schema.TextLine(
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
