# -*- coding: utf-8 -*-
from genweb.tfemarket.content.market import IMarket
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.content.application import IApplication
from genweb.theme.browser.viewlets import packages_installed


def Negotiator(event):
    try:
        packages = packages_installed()
        if 'genweb.tfemarket' in packages:
            context = event.request.get("PUBLISHED", None).context
            if IMarket.providedBy(context) or IOffer.providedBy(context) or IApplication.providedBy(context):
                lang = event.request.get("MERCAT_TFE_LANG", 'ca')
                if lang in ['ca', 'en', 'es']:
                    event.request['LANGUAGE'] = lang
                    event.request.LANGUAGE_TOOL.LANGUAGE = lang
    except:
        pass
