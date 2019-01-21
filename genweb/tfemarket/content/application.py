# -*- coding: utf-8 -*-

from five import grok
from plone import api
from plone.directives import dexterity
from plone.directives import form
from zope import schema

from genweb.tfemarket import _
from genweb.tfemarket.utils import checkPermissionCreateApplications
from genweb.tfemarket.utils import getDegreeLiteralFromId
from genweb.tfemarket.z3cwidget import ReadOnlyInputFieldWidget
from genweb.tfemarket.z3cwidget import StudentInputFieldWidget

from zope.globalrequest import getRequest
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IContextSourceBinder

from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

import ast

grok.templatedir("templates")


@grok.provider(IContextSourceBinder)
def getDregees(context):

    result = []
    titulacions = []
    request = getRequest()

    data = request.cookies.get('APPLICATION_DATA')
    result = ast.literal_eval(data)
    degrees = result['degrees']

    for item in degrees:
        titulacions.append(SimpleTerm(value=item['degree_id'], title=item['degree_title']))

    return SimpleVocabulary(titulacions)


class IApplication(form.Schema):
    """ Application for an offer
    """
    form.mode(degree_title='hidden')
    degree_title = schema.TextLine(
        title=_(u'Title of the degree with which you request the offer'),
        required=False,
    )

    degree_id = schema.Choice(
        title=_(u'Title of the degree with which you request the offer'),
        source=getDregees,
        required=True,
    )

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

    form.mode(codi_expedient='hidden')
    codi_expedient = schema.TextLine(
        title=_(u'Codi Expedient'),
        required=False,
    )

    body = schema.Text(
        title=_(u'Body'),
        required=False,
    )


@grok.subscribe(IApplication, IObjectModifiedEvent)
@grok.subscribe(IApplication, IObjectAddedEvent)
def defineDregreecode(application, event):
    application.degree_title = getDegreeLiteralFromId(application.degree_id)
    application.reindexObject()


class Add(dexterity.AddForm):
    grok.name('application')

    def updateWidgets(self):
        super(Add, self).updateWidgets()
        if not checkPermissionCreateApplications(self, self.context, False):
            self.context.plone_utils.addPortalMessage(_(u"You have already created an application. You can see it on the main page of the market."), 'error')
            self.redirect(self.context.absolute_url())


class View(grok.View):
    grok.require('zope2.View')
    grok.context(IApplication)
    grok.template('application_view')

    def redirectToMarket(self):
        roles = api.user.get_current().getRoles()
        market_path = self.context.getParentNode().getParentNode().absolute_url()
        if 'Manager' in roles or 'TFE Manager' in roles:
            self.redirect(market_path + "?offer=" + self.context.offer_id + "&open=Y")
        else:
            self.redirect(market_path)
