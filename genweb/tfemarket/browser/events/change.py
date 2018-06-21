# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from datetime import date
from datetime import datetime
from plone import api
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

from genweb.tfemarket import _
from genweb.tfemarket.browser.events.data.messages import M1
from genweb.tfemarket.browser.events.data.messages import M2
from genweb.tfemarket.browser.events.data.messages import M3
from genweb.tfemarket.browser.events.data.messages import M4
from genweb.tfemarket.browser.events.data.messages import M5
from genweb.tfemarket.browser.events.data.messages import M6
from genweb.tfemarket.utils import checkOfferhasValidApplications
from genweb.tfemarket.utils import sendMessage

import transaction


def offerHasAnotherApplicationsPending(application):
    wf_tool = getToolByName(application, 'portal_workflow')
    tools = getMultiAdapter((application, getRequest()), name='plone_tools')
    parent = application.getParentNode()
    for offer in parent.getChildNodes():
        if offer.id != application.id:
            offerWorkflow = tools.workflow().getWorkflowsFor(offer)[0]
            offerStatus = wf_tool.getStatusOf(offerWorkflow.id, offer)
            stateID = offerWorkflow['states'][offerStatus['review_state']].id
            if stateID == 'requested':
                return True
    return False


def applicationChanged(application, event):
    """ If genweb.tfemarket.application change WF, sends email.
    """

    lang = api.portal.get_current_language()
    if lang not in ['ca', 'en', 'es']:
        lang = 'en'
    data = {
        'student': application.title,
        'degree': 'Titulació usuari',
        'num': application.getParentNode().offer_id,
        'title': application.getParentNode().title,
        'linkApplication': application.absolute_url(),
        'linkOffer': application.getParentNode().absolute_url(),
        'linkMarket': application.getParentNode().getParentNode().absolute_url(),
        'firm': 'TFE Mercat',
    }

    student_mail = application.email
    teacher_mail = application.getParentNode().teacher_email
    portal = api.portal.get()
    sender_email = portal.getProperty('email_from_address')
    sender_name = portal.getProperty('email_from_name').encode('utf-8')
    email_charset = portal.getProperty('email_charset')

    fromMsg = toMsg = subject = msg = portalMsg = ''
    if event.transition is None:
        # Añadir comprovación de la titulación, en caso de no tener enviar un
        # portal message _(u'A1')
        fromMsg = sender_name + ' ' + '<' + sender_email + '>'
        toMsg = teacher_mail
        subject = _(u'Sol·licita')
        msg = M1[lang].format(**data)
        portalMsg = _(u'A5')
    else:
        if event.transition.id == 'request':
            fromMsg = sender_name + ' ' + '<' + sender_email + '>'
            toMsg = teacher_mail
            subject = _(u'Sol·licita')
            msg = M1[lang].format(**data)
            portalMsg = _(u'A5')
        elif event.transition.id == 'accept':
            fromMsg = sender_name + ' ' + '<' + sender_email + '>'
            toMsg = student_mail
            subject = 'Aceptada'
            msg = M2[lang].format(**data)
            if offerHasAnotherApplicationsPending(application):
                portalMsg = _(u'A6')
        elif event.transition.id == 'reject':
            fromMsg = sender_name + ' ' + '<' + sender_email + '>'
            toMsg = student_mail
            subject = 'Rebutjada'
            msg = M3[lang].format(**data)
        elif event.transition.id == 'confirm':
            fromMsg = sender_name + ' ' + '<' + sender_email + '>'
            toMsg = teacher_mail
            subject = 'Confirma'
            msg = M4[lang].format(**data)
            portalMsg = _(u'A3')
        elif event.transition.id == 'renounce':
            fromMsg = sender_name + ' ' + '<' + sender_email + '>'
            toMsg = teacher_mail
            subject = 'Renuncia'
            msg = M5[lang].format(**data)
            portalMsg = _(u'A4')
        elif event.transition.id == 'cancel':
            fromMsg = sender_name + ' ' + '<' + sender_email + '>'
            toMsg = teacher_mail
            subject = 'Cancela'
            msg = M6[lang].format(**data)

    if not fromMsg == '':
        sendMessage(application, fromMsg, toMsg, subject, msg, email_charset)

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
