# -*- coding: utf-8 -*-

from datetime import date
from datetime import datetime
from plone import api
from Products.CMFCore.utils import getToolByName
from zope.globalrequest import getRequest

from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from genweb.tfemarket.content.offer import IOffer

from genweb.tfemarket.browser.events.messages import M1, M2, M3, M4, M5, M6

from genweb.tfemarket.utils import checkOfferhasValidApplications
from genweb.tfemarket.utils import sendMessage
from genweb.tfemarket import _

import transaction
from five import grok


def applicationChanged(application, event):
    """ If genweb.tfemarket.application change WF, sends email.
    """

    lang = api.portal.get_current_language()
    if lang not in ['ca', 'en', 'es']:
        lang = 'en'
    data = {
        'student': application.fullname,
        'degree': 'Titulació usuari',
        'num': application.getParentNode().offer_id,
        'title': application.getParentNode().title,
        'linkApplication': application.absolute_url(),
        'linkOffer': application.getParentNode().absolute_url(),
        'linkMarket': application.getParentNode().getParentNode().absolute_url(),
        'firm': 'TFE Mercat',
    }

    fromMsg = toMsg = subject = msg = portalMsg = ''
    if event.transition is None:
        # Añadir comprovación de la titulación, en caso de no tener enviar un
        # portal message _(u'A1')
        fromMsg = 'Estudiant'
        toMsg = 'Professor'
        subject = 'Sol·licita'
        msg = M1[lang].format(**data)
        portalMsg = _(u'A5')
    else:
        if event.transition.id == 'request':
            fromMsg = 'Estudiant'
            toMsg = 'Professor'
            subject = 'Sol·licita'
            msg = M1[lang].format(**data)
            portalMsg = _(u'A5')
        elif event.transition.id == 'accept':
            fromMsg = 'Professor'
            toMsg = 'Estudiant'
            subject = 'Aceptada'
            msg = M2[lang].format(**data)
        elif event.transition.id == 'reject':
            fromMsg = 'Professor'
            toMsg = 'Estudiant'
            subject = 'Rebutjada'
            msg = M3[lang].format(**data)
        elif event.transition.id == 'confirm':
            fromMsg = 'Estudiant'
            toMsg = 'Professor'
            subject = 'Confirma'
            msg = M4[lang].format(**data)
            portalMsg = _(u'A3')
        elif event.transition.id == 'renounce':
            fromMsg = 'Estudiant'
            toMsg = 'Professor'
            subject = 'Renuncia'
            msg = M5[lang].format(**data)
            portalMsg = _(u'A4')
        elif event.transition.id == 'cancel':
            fromMsg = 'Estudiant'
            toMsg = 'Professor'
            subject = 'Cancela'
            msg = M6[lang].format(**data)

    if not fromMsg == '':
        sendMessage(application, fromMsg, toMsg, subject, msg)

    if not portalMsg == '':
        application.plone_utils.addPortalMessage(portalMsg, 'info')


def offerChanged(offer, event):
    """ If genweb.tfemarket.offer change WF, checks if expired otherwise we
        will change the effective date.
    """

    if event.transition is not None:
        if event.transition.id in ['publicaalintranet', 'publicaloferta']:
            wftool = getToolByName(offer, 'portal_workflow')
            if offer.expiration_date:
                today = date.today()
                expiration_date = datetime.strptime(offer.expiration_date.Date(), '%Y/%m/%d').date()
                diff_days = expiration_date - today
                if diff_days.days < 0:
                    wftool.doActionFor(offer, 'caducaloferta')
                    transaction.commit()
                else:
                    offer.effective_date = datetime.now()
                    offer.reindexObject()
            else:
                wftool.doActionFor(offer, 'caducaloferta')
                transaction.commit()


def offerCanceled(offer, event):
    """ If genweb.tfemarket.offer change WF, checks if can canceled.
    """

    if event.transition is not None:
        if event.transition.id == 'cancellaloferta':
            if checkOfferhasValidApplications(offer):
                offer.plone_utils.addPortalMessage(_(u'The offer can\'t be canceled if it contains active applications.'), 'info')
                request = getRequest()
                request.response.redirect(offer.absolute_url())


def offerDeleted(offer, event):
    """ Checks if can deleted genweb.tfemarket.offer.
    """

    if checkOfferhasValidApplications(offer):
        offer.plone_utils.addPortalMessage(_(u"The offer can't be deleted."), 'error')
        request = getRequest()
        request.response.redirect(offer.absolute_url())
