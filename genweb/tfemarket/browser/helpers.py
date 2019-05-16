# -*- coding: utf-8 -*-
from Products.statusmessages.interfaces import IStatusMessage
from five import grok
from plone import api
from plone.app.event.base import dt_end_of_day
from plone.app.event.base import dt_start_of_day
from plone.dexterity.utils import createContentInContainer
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.interface import Interface

from genweb.tfemarket.content import IMarket
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
from genweb.tfemarket.utils import getLdapExactUserData

import csv
import datetime
import transaction


class importTitulacions(grok.View):
    """ Import Titulacions from csv file """
    grok.name('import_titulacions')
    grok.context(Interface)
    grok.template('import_titulacions')
    grok.require('cmf.ManagePortal')
    grok.layer(IGenwebTfemarketLayer)

    def update(self):
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            fitxer = self.request.form['degreesfile']
            filename = fitxer.filename

            if filename != '' and filename.endswith('.csv'):
                registry = queryUtility(IRegistry)
                tfe_tool = registry.forInterface(ITfemarketSettings)
                tfe_tool.titulacions_table = []

                csv_file = csv.reader(fitxer, delimiter=',', quotechar='"')
                csv_file.next()  # Ignore header for csv

                for row in csv_file:

                    codi_centre = int(row[0].decode("utf-8"))
                    if not codi_centre == tfe_tool.center_code:
                        continue

                    data = {
                        'codi_prisma': int(row[1].decode("utf-8")),
                        'progam_type': row[2].decode("utf-8"),
                        'codi_mec': row[3].decode("utf-8"),
                        'plan_year': int(row[4].decode("utf-8")),
                        'titulacio_es': row[6].decode("utf-8"),
                        'titulacio_ca': row[5].decode("utf-8"),
                        'titulacio_en': row[7].decode("utf-8"),
                    }

                    tfe_tool.titulacions_table.append(data)

                transaction.commit()
                self.request.response.redirect(self.context.absolute_url() + "/tfemarket-settings#fieldsetlegend-1")
            else:
                message = (u"Falta afegir el fitxer csv.")
                IStatusMessage(self.request).addStatusMessage(message, type='error')


class importOfertes(grok.View):
    """ Import Titulacions from csv file """
    grok.name('import_ofertes')
    grok.context(Interface)
    grok.template('import_ofertes')
    grok.require('cmf.ManagePortal')
    grok.layer(IGenwebTfemarketLayer)

    def update(self):
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            marketUID = self.request.form['market']
            fitxer = self.request.form['offersfile']
            filename = fitxer.filename
            hasHeaders = 'csv_headers' in self.request.form

            if filename != '' and filename.endswith('.csv'):
                msgError = self.createOffers(hasHeaders, fitxer, marketUID)
                if msgError != []:
                    IStatusMessage(self.request).addStatusMessage('\n'.join(msgError), type='error')
                else:
                    self.request.response.redirect(self.context.absolute_url() + "/tfemarket-settings#fieldsetlegend-2")
            else:
                message = (u"Falta afegir el fitxer csv.")
                IStatusMessage(self.request).addStatusMessage(message, type='alert')

    def createOffers(self, hasHeaders, fitxer, marketUID):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)

        catalog = api.portal.get_tool(name='portal_catalog')
        market = catalog(UID=marketUID)[0].getObject()

        msgError = []
        csv_file = csv.reader(fitxer, delimiter=',', quotechar='"')

        if hasHeaders:
            csv_file.next()  # Ignore header for csv

        for count, row in enumerate(csv_file):
            # Importa ofertas
            notValidDegrees = self.checkNotValidDegrees(row[5].decode("utf-8").split(","))
            if len(notValidDegrees) == 0:
                teacher = getLdapExactUserData(row[7].decode("utf-8"))
                if teacher:
                    data = {
                        'title': row[0].decode("utf-8"),
                        'description': row[1].decode("utf-8"),
                        'topic': row[2].decode("utf-8"),
                        'offer_type': row[3].decode("utf-8"),
                        'tfgm': row[4].decode("utf-8").split(","),
                        'degree': row[5].decode("utf-8").split(","),
                        'keys': row[6].decode("utf-8").split(","),
                        'teacher_manager': teacher['id'],
                        'teacher_fullname': teacher['sn1'] + ' ' + teacher['sn2'] + ', ' + teacher['givenName'] if 'sn2' in teacher else teacher['sn1'] + ', ' + teacher['givenName'],
                        'teacher_email': teacher['mail'],
                        'dept': teacher['unitCode'] + "-" + teacher['unit'],
                        'num_students': int(row[10].decode("utf-8")),
                        'workload': row[11].decode("utf-8"),
                        'targets': row[12].decode("utf-8"),
                        'features': row[13].decode("utf-8"),
                        'requirements': row[14].decode("utf-8"),
                        'lang': row[15].decode("utf-8").split(","),
                        'modality': row[16].decode("utf-8"),
                        'co_manager': row[17].decode("utf-8"),
                        'company': row[18].decode("utf-8"),
                        'company_contact': row[19].decode("utf-8"),
                        'company_email': row[20].decode("utf-8"),
                        'grant': bool(row[21].decode("utf-8") == "True"),
                        'confidential': bool(row[22].decode("utf-8") == "True"),
                        'environmental_theme': bool(row[23].decode("utf-8") == "True"),
                        'scope_cooperation': bool(row[24].decode("utf-8") == "True"),
                    }

                    type_codirector = row[8].decode("utf-8")
                    data.update({'type_codirector': type_codirector})
                    if type_codirector == 'UPC':
                        codirector = getLdapExactUserData(row[9].decode("utf-8"))
                        if codirector:
                            data.update({
                                'codirector_id': codirector['id'],
                                'codirector': codirector['sn1'] + ' ' + codirector['sn2'] + ', ' + codirector['givenName'] if 'sn2' in codirector else codirector['sn1'] + ', ' + codirector['givenName'],
                                'codirector_email': codirector['mail'],
                                'codirector_dept': codirector['unitCode'] + "-" + codirector['unit']
                            })
                        else:
                            msg = row[0].decode("utf-8") + " - Codirector (" + row[9].decode("utf-8") + ") not exist."
                            print str(count + 1) + ": Error - " + msg
                            msgError.append(str(count + 1) + ": " + msg)
                            continue
                    else:
                        data.update({'codirector': row[9].decode("utf-8")})

                    offer = createContentInContainer(market, "genweb.tfemarket.offer", **data)
                    offer.setEffectiveDate(dt_start_of_day(datetime.datetime.today() + datetime.timedelta(1)))
                    offer.setExpirationDate(dt_end_of_day(datetime.datetime.today() + datetime.timedelta(365)))
                    offer.reindexObject()

                    # Importa topics y tags
                    strTopics = row[2].decode("utf-8") + ","
                    topics = list(dict.fromkeys(strTopics.split(",")[:-1]))
                    actualTopics = tfe_tool.topics.split('\r\n')
                    newTopics = "\r\n".join([topic for topic in topics if topic not in actualTopics])
                    if newTopics:
                        tfe_tool.topics += "\r\n" + newTopics

                    strTags = row[6].decode("utf-8") + ","
                    tags = list(dict.fromkeys(strTags.split(",")[:-1]))
                    actualTags = tfe_tool.tags.split('\r\n')
                    newTags = "\r\n".join([tag for tag in tags if tag not in actualTags])
                    if newTags:
                        tfe_tool.tags += "\r\n" + newTags

                    transaction.commit()

                    print str(count + 1) + ": Done - " + row[0].decode("utf-8")
                else:
                    msg = row[0].decode("utf-8") + " - Teacher (" + row[7].decode("utf-8") + ") not exist."
                    print str(count + 1) + ": Error - " + msg
                    msgError.append(str(count + 1) + ": " + msg)
            else:
                msg = row[0].decode("utf-8") + " - Degree (" + " - ".join(notValidDegrees) + ") not valid."
                print str(count + 1) + ": Error - " + msg
                msgError.append(str(count + 1) + ": " + msg)

        return msgError

    def getMarkets(self):
        markets = []
        catalog = api.portal.get_tool(name='portal_catalog')
        values = catalog(path={'query': '/'},
                         object_provides=IMarket.__identifier__)
        for market in values:
            markets.append({'value': market.UID, 'title': market.Title})

        return markets

    def checkNotValidDegrees(self, degrees):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        allDegrees = [x['codi_mec'] for x in tfe_tool.titulacions_table]
        notValid = [x for x in degrees if x not in allDegrees]
        return notValid
