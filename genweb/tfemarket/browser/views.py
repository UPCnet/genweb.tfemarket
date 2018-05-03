# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from five import grok
from plone import api
from zope.interface import Interface

from genweb.tfemarket import _
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
from genweb.tfemarket.utils import getLdapExactUserData
from genweb.tfemarket.utils import getLdapUserData

import json


def redirectAfterChangeActualState(self):
    try:
        from plone.protect.interfaces import IDisableCSRFProtection
        alsoProvides(self.request, IDisableCSRFProtection)
    except:
        pass

    if self.context.portal_type == 'genweb.tfemarket.offer':
        self.request.response.redirect(self.context.absolute_url() + '#offer-applications')
    elif self.context.portal_type == 'genweb.tfemarket.market':
        if 'allOffersTeacher' not in self.request.form:
            self.request.response.setCookie('MERCAT_TFE', clearFiltersCookie(self), path='/')
            self.request.response.redirect(self.context.absolute_url())
        else:
            url = self.context.absolute_url() + "?allOffersTeacher"
            if 'offer' in self.request.form:
                url += "&offer=" + self.request.form.get('offer')
            self.request.response.redirect(url)
    else:
        self.request.response.redirect(self.context.absolute_url())


def clearFiltersCookie(self):
    filters = self.request.form
    filters.pop('estat', None)
    filters.pop('id', None)
    filters.pop('_authenticator', None)
    return filters


class changeActualState(grok.View):
    grok.context(Interface)
    grok.name('changeActualState')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)
    """ Es fa servir a la vista sessio i presentacio. No cal fer reload perque
        es mostra el nou valor per JS
    """

    def render(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass

        portal_catalog = getToolByName(self, 'portal_catalog')
        estat = self.request.form.get('estat')
        itemid = self.request.form.get('id')

        try:
            portal = api.portal.get()
            currentitem = portal.unrestrictedTraverse(itemid)
            if currentitem:
                wftool = getToolByName(self.context, 'portal_workflow')
                wftool.doActionFor(currentitem, estat)
                redirectAfterChangeActualState(self)
            else:
                self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
                redirectAfterChangeActualState(self)

        except:
            self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
            redirectAfterChangeActualState(self)


class getTeacher(grok.View):
    grok.context(Interface)
    grok.name('getTeacher')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        ### TODO Cambiar PERSONAL por PDI
        # teachers = getLdapUserData(self.request.form['teacher'], typology='PERSONAL')
        teachers = getLdapUserData(self.request.form['teacher'])
        if len(teachers) > 0:
            listTeachers = []
            for teacher in teachers:
                try:
                    teacherDept = teacher['unitCode'] + "-" + teacher['unit']
                    listTeachers.append({
                        'user': teacher['id'],
                        'email': teacher['mail'],
                        'fullname': teacher['sn'],
                        'dept': teacherDept
                    })
                except:
                    pass
            return json.dumps(listTeachers)
        else:
            return None


class getExactTeacher(grok.View):
    grok.context(Interface)
    grok.name('getExactTeacher')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        ### TODO Cambiar PERSONAL por PDI
        # teacher = getLdapExactUserData(self.request.form['teacher'], typology='PERSONAL')
        teacher = getLdapExactUserData(self.request.form['teacher'])
        if teacher and 'sn' in teacher:
            teacherDept = teacher['unitCode'] + "-" + teacher['unit']
            data = {
                'user': teacher['id'],
                'email': teacher['mail'],
                'fullname': teacher['sn'],
                'dept': teacherDept
            }
            return json.dumps(data)
        else:
            return None
