# -*- coding: utf-8 -*-

from datetime import date
from datetime import datetime
from Products.CMFCore.utils import getToolByName

from genweb.tfemarket.utils import sendMessage
from genweb.tfemarket import _

import transaction


def applicationChanged(application, event):
    """ If genweb.tfemarket.application change WF, sends email.
    """

    fromMsg = toMsg = subject = msg = portalMsg = ''
    if event.transition is None:
        fromMsg = 'Estudiant'
        toMsg = 'Professor'
        subject = 'Sol·licita'
        msg = 'M1'
    else:
        if event.transition.id == 'request':
            fromMsg = 'Estudiant'
            toMsg = 'Professor'
            subject = 'Sol·licita'
            msg = 'M1'
        elif event.transition.id == 'accept':
            fromMsg = 'Professor'
            toMsg = 'Estudiant'
            subject = 'Aceptada'
            msg = 'M2'
        elif event.transition.id == 'reject':
            fromMsg = 'Professor'
            toMsg = 'Estudiant'
            subject = 'Rebutjada'
            msg = 'M3'
        elif event.transition.id == 'confirm':
            fromMsg = 'Estudiant'
            toMsg = 'Professor'
            subject = 'Confirma'
            msg = 'M4'
            portalMsg = _(u'A3: Confirm offer')
        elif event.transition.id == 'renounce':
            fromMsg = 'Estudiant'
            toMsg = 'Professor'
            subject = 'Renuncia'
            msg = 'M5'
            portalMsg = _(u'A4: Renounce offer')
        elif event.transition.id == 'cancel':
            fromMsg = 'Estudiant'
            toMsg = 'Professor'
            subject = 'Cancela'
            msg = 'M6'

    if not fromMsg == '':
        sendMessage(application, fromMsg, toMsg, subject, msg)

    if not portalMsg == '':
        application.plone_utils.addPortalMessage(portalMsg, 'info')


def offerChanged(offer, event):
    """ If genweb.tfemarket.offer change WF, checks if expired.
    """
    if event.transition is not None:
        if event.transition.id == 'publicaalintranet' or event.transition.id == 'publicaloferta':
            wftool = getToolByName(offer, 'portal_workflow')
            if offer.expiration_date:
                today = date.today()
                expiration_date = datetime.strptime(offer.expiration_date.Date(), '%Y/%m/%d').date()
                diff_days = expiration_date - today
                if diff_days.days < 0:
                    wftool.doActionFor(offer, 'caducaloferta')
                    transaction.commit()
            else:
                wftool.doActionFor(offer, 'caducaloferta')
                transaction.commit()
