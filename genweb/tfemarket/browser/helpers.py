# -*- coding: utf-8 -*-
from five import grok
from plone import api
from zope.interface import Interface
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
from souper.soup import get_soup
import unicodedata
import json
import csv

from Products.statusmessages.interfaces import IStatusMessage
from genweb.core.gwuuid import IGWUUID
from repoze.catalog.query import Eq


class migrateGroups(grok.View):
    """ Import Titulacions from csv file """
    grok.name('import_titulacions')
    grok.context(Interface)
    grok.template('import_titulacions')
    grok.layer(IGenwebTfemarketLayer)

    def update(self):
        self.roles = ''
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            if self.request.form['titulacionsfile'].filename != '':
                fitxer = self.request.form['titulacionsfile']
                titulacions = {}
                for line in fitxer:
                    import ipdb; ipdb.set_trace()
                    row = line.strip().split(';')

                    name_old = row[0].decode("utf-8")
                    name_new = row[1].decode("utf-8")

                pc = api.portal.get_tool(name='portal_catalog')

                self.context.plone_log('Buscant objectes a migrar')
                results = pc.searchResults()
                roles_anteriors = {}
                for num, item in enumerate(results):
                    self.context.plone_log('Processant {} de {}'.format(num, len(results)))
                    obj = item.getObject()
                    roles = obj.get_local_roles()
                    roles_anteriors[item.getPath()] = roles
                    new_roles = dict([(groups.get(rolename, rolename), roleslist) for rolename, roleslist in roles])
                    obj.__ac_local_roles__ = new_roles
                    obj.reindexObjectSecurity()

                roles_anteriors_comunitats = {}
                self.context.plone_log('Buscant permisos comunitats a migrar')
                comunnities = pc.searchResults(portal_type="ulearn.community")
                for num, community in enumerate(comunnities):
                    self.context.plone_log('Processant {} de {}'.format(num, len(comunnities)))
                    obj = community.getObject()
                    gwuuid = IGWUUID(obj).get()
                    portal = api.portal.get()
                    soup = get_soup('communities_acl', portal)

                    records = [r for r in soup.query(Eq('gwuuid', gwuuid))]

                message = (u"La migració ha finalitzat.")
                IStatusMessage(self.request).addStatusMessage(message, type='info')

                self.roles = json.dumps(roles_anteriors)
            else:
                message = (u"Falta afegir el fitxer.")
                IStatusMessage(self.request).addStatusMessage(message, type='error')
