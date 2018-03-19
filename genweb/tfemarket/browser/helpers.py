# -*- coding: utf-8 -*-
from five import grok
from plone.registry.interfaces import IRegistry
from zope.interface import Interface
from zope.component import queryUtility
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
import csv
import transaction

from Products.statusmessages.interfaces import IStatusMessage


class importTitulacions(grok.View):
    """ Import Titulacions from csv file """
    grok.name('import_titulacions')
    grok.context(Interface)
    grok.template('import_titulacions')
    grok.layer(IGenwebTfemarketLayer)

    def update(self):
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            fitxer = self.request.form['titulacionsfile']
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
                        'codi_mec': int(row[3].decode("utf-8")),
                        'plan_year': int(row[4].decode("utf-8")),
                        'titulacio_es': row[5].decode("utf-8"),
                        'titulacio_ca': row[7].decode("utf-8"),
                        'titulacio_en': row[9].decode("utf-8"),
                    }

                    tfe_tool.titulacions_table.append(data)

                transaction.commit()
                self.request.response.redirect(self.context.absolute_url() + "/tfemarket-settings#fieldsetlegend-2")
            else:
                message = (u"Falta afegir el fitxer csv.")
                IStatusMessage(self.request).addStatusMessage(message, type='error')
