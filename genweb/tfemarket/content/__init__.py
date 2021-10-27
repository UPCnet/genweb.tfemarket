# -*- coding: utf-8 -*-

from zope.interface import implements
from plone.dexterity.content import Container
from plone.dexterity.content import Item


from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.content.market import IMarket


class Application(Item):
    implements(IApplication)


class Offer(Container):
    implements(IOffer)


class Market(Container):
    implements(IMarket)
