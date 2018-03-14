# -*- coding: utf-8 -*-

from zope import schema
from plone.supermodel import model
from plone.app.registry.browser import controlpanel

from plone.directives import form
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow

from genweb.tfemarket import _


class ITableTitulacions(form.Schema):

    codi_prisma = schema.Int(
        title=_(u'PRISMA code'),
        required=False,
        description=_(u'Degree code at PRISMA')
    )

    progam_type = schema.TextLine(
        title=_(u'Program type'),
        required=False
    )

    email = schema.TextLine(
        title=_(u'E-mail'),
        required=False
    )

    codi_mec = schema.Int(
        title=_(u'MEC code'),
        required=False,
        description=_(u'MEC degree code')
    )

    plan_year = schema.Int(
        title=_(u'Plan year'),
        required=False,
    )

    titulacio_es = schema.TextLine(
        title=_(u'Titulacions ES'),
        description=_(u''),
        required=False
    )

    titulacio_ca = schema.TextLine(
        title=_(u'Titulacions CA'),
        description=_(u''),
        required=False
    )

    titulacio_en = schema.TextLine(
        title=_(u'Titulacions EN'),
        description=_(u''),
        required=False
    )


class ITfemarketSettings(model.Schema):
    """ Global TFE Market settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    model.fieldset(
        'Settings',
        _(u'Settings'),
        fields=['center_code', 'center_name', 'review_state'],
    )

    model.fieldset(
        'TopicTFE',
        _(u'classifications'),
        fields=['topics', 'tags'],
    )

    model.fieldset(
        'Titulacions',
        _(u'Titulacions'),
        fields=['titulacions_table'],
    )

    # SETTINGS

    center_code = schema.Int(
        title=_(u'Center code'),
        required=False,
        description=_(u'Center code')
    )

    center_name = schema.TextLine(
        title=_(u"Name center"),
        required=False,
    )

    review_state = schema.Bool(title=_(u"Review State"),
                               default=False,
                               description=_(u'Select if you want to add "Reviewer" role'),
                               required=False,
                               )

    # languages = schema.Text(
    #     title=_(u"available_languages",
    #             default=u"Available languages"),
    #     description=_(u"help_available_languages",
    #                   default=u"Languages develop TFE"),
    #     value_type=schema.Choice(vocabulary='plone.app.vocabularies.SupportedContentLanguages'),
    #     required=False,
    #     default=['ca']
    # )

    # CLASSIFICATIONS

    topics = schema.TextLine(
        title=_(u"Topics of the TFE"),
        required=False,
    )

    tags = schema.TextLine(
        title=_(u"Tags"),
        required=False,
    )

    # TITULACIONS

    form.widget(titulacions_table=DataGridFieldFactory)
    titulacions_table = schema.List(title=_(u'Titulacions'),
                                    description=_(u'help_titulacions_table',
                                    default=u'Imported dades from csv'),
                                    value_type=DictRow(title=_(u'titulacionstable'),
                                                       schema=ITableTitulacions),
                                    required=False
                                    )


class TfemarketSettingsEditForm(controlpanel.RegistryEditForm):

    schema = ITfemarketSettings
    label = _(u'UPC Mercat TFE')


class TfemarketSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = TfemarketSettingsEditForm
