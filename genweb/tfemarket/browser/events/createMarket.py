# -*- coding: utf-8 -*-

from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.dexterity.utils import createContentInContainer
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes

from genweb.tfemarket.browser.events.data.folderStructure import folder_structure


def createContentInFolder(folder_directori, folder_content):
    # Create content
    if folder_content[1] != "Folder":
        content_props = {
            'title': folder_content[0],
            'checkConstraints': False,
            'exclude_from_nav': folder_content[2],
            'allow_discussion': folder_content[3]}
        if folder_content[6] is not None:
            content_props['description'] = folder_content[6]
        if folder_content[7] is not None:
            content_props['text'] = IRichText['text'].fromUnicode(folder_content[7])
        if folder_content[5] is not None:
            content_props['layout'] = folder_content[5]
        content = createContentInContainer(
            folder_directori, folder_content[1], **content_props)
        if folder_content[4] is not None:
            behavior = ISelectableConstrainTypes(content)
            behavior.setConstrainTypesMode(1)
            behavior.setLocallyAllowedTypes(folder_content[4])
            behavior.setImmediatelyAddableTypes(folder_content[4])
    else:
        createFolderAndContents(folder_directori, folder_content)


def createFolderAndContents(folder_directori, folder_data):
    # Create folder
    folder_props = {
        'title': folder_data[0],
        'checkConstraints': False,
        'exclude_from_nav': folder_data[2],
        'allow_discussion': folder_data[3]}
    if folder_data[5] is not None:
        folder_props['layout'] = folder_data[5]
    folder = createContentInContainer(folder_directori, folder_data[1], **folder_props)

    behavior = ISelectableConstrainTypes(folder)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(folder_data[4])
    behavior.setImmediatelyAddableTypes(folder_data[4])
    folder.reindexObject()

    # Create a contents
    for folder_content in folder_data[7]:
        createContentInFolder(folder, folder_content)

    if folder_data[6] is not None:
        folder.setDefaultPage(folder_data[6])


def createMarket(market, event):
    for folder_data in folder_structure:
        createFolderAndContents(market, folder_data)
