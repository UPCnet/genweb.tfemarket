# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from datetime import date
from datetime import datetime
from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.globalrequest import getRequest

from genweb.tfemarket import _
from genweb.tfemarket.browser.events.data.messages import M1
from genweb.tfemarket.browser.events.data.messages import M2
from genweb.tfemarket.browser.events.data.messages import M3
from genweb.tfemarket.browser.events.data.messages import M4
from genweb.tfemarket.browser.events.data.messages import M5
from genweb.tfemarket.browser.events.data.messages import M6
from genweb.tfemarket.controlpanel import IBUSSOASettings
from genweb.tfemarket.utils import BusError
from genweb.tfemarket.utils import checkOfferhasValidApplications
from genweb.tfemarket.utils import sendMessage

import requests
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


def offerRegistered(offer, event):
    """ If genweb.tfemarket.offer change WF, checks if registered.
    """

    if event.transition is not None:
        if event.transition.id in ['register', 'registralofertaintranet']:
            registry = queryUtility(IRegistry)
            bussoa_tool = registry.forInterface(IBUSSOASettings)
            bussoa_url = bussoa_tool.bus_url
            bussoa_user = bussoa_tool.bus_user
            bussoa_pass = bussoa_tool.bus_password
            bussoa_apikey = bussoa_tool.bus_apikey

            # ONLY FOR TRY #####################

            list_test = [{'id_prisma': '2866124', 'numDocument': '44522242S'},
                         {'id_prisma': '2708530', 'numDocument': '47405847H'},
                         {'id_prisma': '2708479', 'numDocument': '41747970A'},
                         {'id_prisma': '2707723', 'numDocument': '18079004S'},
                         {'id_prisma': '2706798', 'numDocument': '48085070M'},
                         {'id_prisma': '2554111', 'numDocument': '53870113L'},
                         {'id_prisma': '2553255', 'numDocument': '39934092C'},
                         {'id_prisma': '2553249', 'numDocument': '53835514N'},
                         {'id_prisma': '2553092', 'numDocument': '26063484E'},
                         {'id_prisma': '2552221', 'numDocument': '21798723J'},
                         {'id_prisma': '2551839', 'numDocument': 'X2756193B'},
                         {'id_prisma': '2551740', 'numDocument': '73461145L'},
                         {'id_prisma': '2551700', 'numDocument': '41578237X'},
                         {'id_prisma': '2551388', 'numDocument': '47238061V'},
                         {'id_prisma': '2550963', 'numDocument': '48031179A'},
                         {'id_prisma': '2550923', 'numDocument': '79272419K'},
                         {'id_prisma': '2550789', 'numDocument': '53316254T'},
                         {'id_prisma': '2438885', 'numDocument': 'Y3346939Q'},
                         {'id_prisma': '2433865', 'numDocument': '70077461A'},
                         {'id_prisma': '2407950', 'numDocument': '05315643K'},
                         {'id_prisma': '2407902', 'numDocument': '41574784F'},
                         {'id_prisma': '2401711', 'numDocument': '47322096X'},
                         {'id_prisma': '2401541', 'numDocument': '77624311R'},
                         {'id_prisma': '2400827', 'numDocument': '17765920F'},
                         {'id_prisma': '2400653', 'numDocument': '47835848B'},
                         {'id_prisma': '2400648', 'numDocument': '48032008G'},
                         {'id_prisma': '2400208', 'numDocument': '39936041Z'},
                         {'id_prisma': '2400053', 'numDocument': '48037883Z'},
                         {'id_prisma': '2399504', 'numDocument': '25624813F'},
                         {'id_prisma': '2399333', 'numDocument': '45126841J'},
                         {'id_prisma': '2399207', 'numDocument': '47332956Z'},
                         {'id_prisma': '2399205', 'numDocument': '41597001Y'},
                         {'id_prisma': '2399187', 'numDocument': 'Y3541903D'},
                         {'id_prisma': '2398864', 'numDocument': '48037052B'},
                         {'id_prisma': '2398761', 'numDocument': '43575236B'},
                         {'id_prisma': '2398743', 'numDocument': '05458237S'},
                         {'id_prisma': '2398335', 'numDocument': '53292318F'},
                         {'id_prisma': '2398310', 'numDocument': '48090627L'},
                         {'id_prisma': '2398303', 'numDocument': '46414025W'},
                         {'id_prisma': '2398292', 'numDocument': '21780110F'},
                         {'id_prisma': '2398291', 'numDocument': '53869317M'},
                         {'id_prisma': '2398187', 'numDocument': '48019958Y'},
                         {'id_prisma': '2398145', 'numDocument': '47838860X'},
                         {'id_prisma': '2398058', 'numDocument': '48099790M'},
                         {'id_prisma': '2397841', 'numDocument': '23878574C'},
                         {'id_prisma': '2397674', 'numDocument': '47592922B'},
                         {'id_prisma': '2397654', 'numDocument': '43460008J'},
                         {'id_prisma': '2397644', 'numDocument': '48026090C'},
                         {'id_prisma': '2397485', 'numDocument': '43570423M'},
                         {'id_prisma': '2381463', 'numDocument': '47838895E'},
                         {'id_prisma': '2201379', 'numDocument': '41586362Q'},
                         {'id_prisma': '2195877', 'numDocument': '49876030R'},
                         {'id_prisma': '2184958', 'numDocument': '24412328J'},
                         {'id_prisma': '2174310', 'numDocument': '41549964G'},
                         {'id_prisma': '2174137', 'numDocument': '41583105W'},
                         {'id_prisma': '2173869', 'numDocument': '47962264L'},
                         {'id_prisma': '2173315', 'numDocument': '53399800X'},
                         {'id_prisma': '2167398', 'numDocument': '41577897S'},
                         {'id_prisma': '2167393', 'numDocument': '41645490B'},
                         {'id_prisma': '2166968', 'numDocument': '43230795H'},
                         {'id_prisma': '2166671', 'numDocument': '73221885M'},
                         {'id_prisma': '2166442', 'numDocument': '47929763V'},
                         {'id_prisma': '2166329', 'numDocument': '23821903K'},
                         {'id_prisma': '2166157', 'numDocument': '41600603C'},
                         {'id_prisma': '2166145', 'numDocument': '48036709J'},
                         {'id_prisma': '2166067', 'numDocument': '48270505Z'},
                         {'id_prisma': '2166005', 'numDocument': '39406537Q'},
                         {'id_prisma': '2165889', 'numDocument': '53866745D'},
                         {'id_prisma': '2165617', 'numDocument': '49285361H'},
                         {'id_prisma': '2165370', 'numDocument': '48138659G'},
                         {'id_prisma': '2164977', 'numDocument': '43636007Q'},
                         {'id_prisma': '2164887', 'numDocument': '48022181K'},
                         {'id_prisma': '2164805', 'numDocument': '39391127Q'},
                         {'id_prisma': '2164558', 'numDocument': '48097958J'},
                         {'id_prisma': '2164458', 'numDocument': '43205827M'},
                         {'id_prisma': '2164383', 'numDocument': '23821727Y'},
                         {'id_prisma': '2164117', 'numDocument': '46494260J'},
                         {'id_prisma': '2164001', 'numDocument': '45648881E'},
                         {'id_prisma': '2163975', 'numDocument': '45790582C'},
                         {'id_prisma': '2163779', 'numDocument': '23302009L'},
                         {'id_prisma': '2163595', 'numDocument': '47894493Y'},
                         {'id_prisma': '1953736', 'numDocument': 'Y0725916G'},
                         {'id_prisma': '1920503', 'numDocument': '47852616N'},
                         {'id_prisma': '1908655', 'numDocument': '47691604T'},
                         {'id_prisma': '1908273', 'numDocument': '48103682X'},
                         {'id_prisma': '1907783', 'numDocument': '39409440K'},
                         {'id_prisma': '1907709', 'numDocument': '48235146Y'},
                         {'id_prisma': '1907406', 'numDocument': '47276068M'},
                         {'id_prisma': '1907372', 'numDocument': '45832949K'}]

            from random import randint
            test_user = list_test[randint(0, len(list_test) - 1)]
            id_prisma = test_user['id_prisma']

            datos_json = {
                "codiExpedient": "303023",
                "codiPrograma": "22500733",
                "codiOferta": "3",
                "titol": "lalalala",
                "modalitat": "5",
                "director": "6",
                "departament": "7",
                "numDocument": "53316254T",
                "descripcio": "9",
                "idiomaTreball": "10",
                "propostaAmbitCooperacio": "11",
                "tematicaAmbiental": "12",
                "centre": "13",
                "codirector": "14",
                "empresa": "15",
                "personaContacteEmpresa": "16",
                "confidencial": "17",
                "tipusAltaTFE": "I"
            }

            res_aplic = requests.put(bussoa_url + "%s" % id_prisma, headers={'apikey': bussoa_apikey}, auth=(bussoa_user, bussoa_pass), json=datos_json)
            if res_aplic.status_code != 200:
                raise BusError(res_aplic)

            return res_aplic
