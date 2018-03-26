# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName


class changeActualState(BrowserView):
    """ Es fa servir a la vista sessio i presentacio. No cal fer reload perque
        es mostra el nou valor per JS
    """
    def __call__(self):
        portal_catalog = getToolByName(self, 'portal_catalog')
        estat = self.request.form.get('estat')
        itemid = self.request.form.get('id')
        try:
            object_path = '/'.join(self.context.getPhysicalPath())
            item = str(itemid.split('/')[-1:][0])
            currentitem = portal_catalog.searchResults(
                portal_type=['genweb.tfemarket.application', 'genweb.tfemarket.offer'],
                id=item,
                path={'query': object_path,
                      'depth': 1})[0].getObject()

            wftool = getToolByName(self.context, 'portal_workflow')
            wftool.doActionFor(currentitem, estat)

            if self.context.portal_type == 'genweb.tfemarket.offer':
                self.request.response.redirect(self.context.absolute_url() + "#offer-applications")
            else:
                self.request.response.redirect(self.context.absolute_url())

        except:
            pass
