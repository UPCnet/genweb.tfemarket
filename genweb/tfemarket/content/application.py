# -*- coding: utf-8 -*-

from five import grok
from plone import api
from plone.app.textfield import RichText as RichTextField
from plone.autoform import directives
from plone.dexterity.utils import createContentInContainer
from plone.directives import dexterity
from plone.directives import form
from zope import schema

from genweb.tfemarket import _
from genweb.tfemarket.utils import checkPermissionCreateApplications
from genweb.tfemarket.utils import getLdapExactUserData

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
        else:
            current = api.user.get_current()
            user = getLdapExactUserData(current.id)
            if user and 'sn' in user:
                data = {
                    'offer_id': self.context.offer_id,
                    'offer_title': self.context.title,
                    'title': user['sn'],
                    'dni': user['DNIpassport'],
                    'email': user['mail'],
                }

                if 'telephoneNumber' in user:
                    data.update({'phone': user['telephoneNumber']})

                app = createContentInContainer(self.context, "genweb.tfemarket.application", **data)
                app.reindexObject()
                self.redirect(app.absolute_url())
            else:
                self.context.plone_utils.addPortalMessage(_(u"User not exist in LDAP."), 'error')
                self.redirect(self.context.absolute_url())


class View(grok.View):
    grok.context(IApplication)
    grok.template('application_view')
