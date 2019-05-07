# -*- coding: utf-8 -*-

from five import grok
from operator import itemgetter
from plone import api
from plone.autoform import directives
from plone.directives import dexterity
from plone.directives import form
from plone.indexer import indexer
from plone.registry.interfaces import IRegistry
from z3c.form import field
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.component import queryUtility
from zope.i18n import translate
from zope.interface import Invalid
from zope.interface import invariant
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from genweb.tfemarket import _
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.validations import validateEmail
from genweb.tfemarket.z3cwidget import FieldsetFieldWidget
from genweb.tfemarket.z3cwidget import ReadOnlyInputFieldWidget
from genweb.tfemarket.z3cwidget import SelectModalityInputFieldWidget
from genweb.tfemarket.z3cwidget import TeacherInputFieldWidget

import transaction
import unicodedata


grok.templatedir("templates")


class LangsVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        results = tfe_tool.languages

        lang = api.portal.get_current_language()

        languages = []
        for item in results:
            if isinstance(item, str):
                flattened = unicodedata.normalize('NFKD', item.decode(
                    'utf-8')).encode('ascii', errors='ignore')
            else:
                flattened = unicodedata.normalize('NFKD', item).encode('ascii', errors='ignore')

            itemTranslate = translate(msgid=item, domain='genweb.tfemarket', target_language=lang)
            languages.append(SimpleVocabulary.createTerm(item, flattened, itemTranslate))

        return SimpleVocabulary(languages)


grok.global_utility(LangsVocabulary, name=u"genweb.tfemarket.Langs")


class KeysVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        results = []
        tags = []

        keys = tfe_tool.tags
        if keys:
            results = keys.split("\r\n")

        for item in results:
            if isinstance(item, str):
                flattened = unicodedata.normalize('NFKD', item.decode(
                    'utf-8')).encode('ascii', errors='ignore')
            else:
                flattened = unicodedata.normalize('NFKD', item).encode('ascii', errors='ignore')
            tags.append(SimpleVocabulary.createTerm(item, flattened, item))

        return SimpleVocabulary(tags)


grok.global_utility(KeysVocabulary, name=u"genweb.tfemarket.Keys")


class TopicsVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        results = []
        topic = []

        topics = tfe_tool.topics
        if topics:
            results = topics.split("\r\n")

        for item in results:
            if isinstance(item, str):
                flattened = unicodedata.normalize('NFKD', item.decode(
                    'utf-8')).encode('ascii', errors='ignore')
            else:
                flattened = unicodedata.normalize('NFKD', item).encode('ascii', errors='ignore')
            topic.append(SimpleVocabulary.createTerm(item, flattened, item))

        return SimpleVocabulary(topic)


grok.global_utility(TopicsVocabulary, name=u"genweb.tfemarket.Topics")


class OfferTypesVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        types = []
        types.append(SimpleVocabulary.createTerm(u'Study', 'Study', _(u'Study')))
        types.append(SimpleVocabulary.createTerm(u'Project', 'Project', _(u'Project')))
        types.append(SimpleVocabulary.createTerm(u'Design', 'Design', _(u'Design')))
        types.append(SimpleVocabulary.createTerm(u'Others', 'Others', _(u'Others')))
        return SimpleVocabulary(types)


grok.global_utility(OfferTypesVocabulary, name=u"genweb.tfemarket.OfferTypes")


class DegreesVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        current_language = api.portal.get_current_language()

        result = []
        titulacions = []

        for item in tfe_tool.titulacions_table:
            titulacio = str(item['plan_year']) + " - "
            if current_language == 'ca':
                titulacio += item['titulacio_ca']
            elif current_language == 'es':
                titulacio += item['titulacio_es']
            else:
                titulacio += item['titulacio_en']

            result.append({'id': item['codi_mec'], 'lit': titulacio})

        result = sorted(result, key=itemgetter('lit'))

        for item in result:
            titulacions.append(SimpleTerm(value=item['id'], title=item['lit']))

        return SimpleVocabulary(titulacions)


grok.global_utility(DegreesVocabulary, name=u"genweb.tfemarket.Titulacions")


class IOffer(form.Schema):
    """ Folder that contains information about a TFE and its applications
    """

    form.mode(center='hidden')
    center = schema.TextLine(
        title=_(u'offer_center'),
        required=False,
    )

    directives.mode(offer_id="hidden")
    offer_id = schema.TextLine(
        title=_(u'Offer id'),
        required=False,
    )

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Description'),
        required=True,
    )

    topic = schema.Choice(
        title=_(u'offer_topic'),
        vocabulary=u"genweb.tfemarket.Topics",
        required=False
    )

    offer_type = schema.Choice(
        title=_(u'offer_type'),
        vocabulary=u"genweb.tfemarket.OfferTypes",
        default=_(u'Project'),
        required=False
    )

    form.widget(degree=CheckBoxFieldWidget)
    degree = schema.List(
        value_type=schema.Choice(source=u"genweb.tfemarket.Titulacions"),
        title=_(u'degree'),
        required=True,
    )

    form.widget(keys=CheckBoxFieldWidget)
    keys = schema.List(
        value_type=schema.Choice(source=u"genweb.tfemarket.Keys"),
        title=_(u'keys'),
        required=False,
    )

    ############################################################################

    form.widget('fieldset_dir', FieldsetFieldWidget)
    fieldset_dir = schema.Text(
        default=_(u'Direction'),
        required=False,
    )

    form.widget('teacher_manager', TeacherInputFieldWidget)
    teacher_manager = schema.TextLine(
        title=_(u'TFEteacher'),
        required=True,
    )

    form.widget('teacher_fullname', ReadOnlyInputFieldWidget)
    teacher_fullname = schema.TextLine(
        title=_(u'Teacher Fullname'),
        required=False,
    )

    form.widget('teacher_email', ReadOnlyInputFieldWidget)
    teacher_email = schema.TextLine(
        title=_(u'Teacher Email'),
        required=False,
    )

    form.widget('dept', ReadOnlyInputFieldWidget)
    dept = schema.TextLine(
        title=_(u'University department'),
        required=False,
    )

    codirector = schema.Text(
        title=_(u'Codirector'),
        required=False,
    )

    ############################################################################

    form.widget('fieldset_req', FieldsetFieldWidget)
    fieldset_req = schema.Text(
        default=_(u'Other data'),
        required=False,
    )

    num_students = schema.Int(
        title=_(u'Number of students'),
        description=_(u'Màxim segons normativa del centre'),
        default=1,
        min=1,
        max=10,
        required=True,
    )

    workload = schema.TextLine(
        title=_(u'offer_workload'),
        description=_(u'Un crèdit ECTS equival a 25 hores de treball'),
        default=_(u'La càrrega de treball s\'adptarà als crèdits de la titulació.'),
        required=True,
    )

    targets = schema.Text(
        title=_(u'offer_targets'),
        required=False,
    )

    features = schema.Text(
        title=_(u'offer_features'),
        required=False,
    )

    requirements = schema.Text(
        title=_(u'requirements'),
        required=False,
    )

    form.widget(lang=CheckBoxFieldWidget)
    lang = schema.List(
        value_type=schema.Choice(vocabulary=u"genweb.tfemarket.Langs"),
        title=_(u'tfe_lang'),
        required=True,
        default=['CA']
    )

    ############################################################################

    form.widget('fieldset_mod', FieldsetFieldWidget)
    fieldset_mod = schema.Text(
        default=_(u'Modality'),
        required=False,
    )

    form.widget('modality', SelectModalityInputFieldWidget)
    modality = schema.Choice(
        title=_(u'modality'),
        values=[u'Universitat',
                u'Empresa'],
        default=_(u'Universitat'),
        required=True,
    )

    co_manager = schema.TextLine(
        title=_(u'CoManager'),
        required=False,
    )

    company = schema.TextLine(
        title=_(u'Company'),
        required=False,
    )

    company_contact = schema.TextLine(
        title=_(u'Company Contact'),
        required=False,
    )

    company_email = schema.TextLine(
        title=_(u'Company Email'),
        required=False,
        constraint=validateEmail,
    )

    @invariant
    def validate_isFull(data):
        if data.modality == 'Empresa' and not (data.co_manager and data.company and data.company_contact and data.company_email):
            raise Invalid(_(u"Falta omplir les dades d'empresa"))
        if not data.lang:
            raise Invalid(_(u'Falta omplir "Idioma del treball"'))

    ############################################################################

    form.widget('fieldset_opt', FieldsetFieldWidget)
    fieldset_opt = schema.Text(
        default=_(u'Options'),
        required=False,
    )

    grant = schema.Bool(
        title=_(u'Possibility of scholarship'),
        required=False,
        default=False,
    )

    confidential = schema.Bool(
        title=_(u'confidential'),
        default=False,
        required=False,
    )

    environmental_theme = schema.Bool(
        title=_(u'Environmental Theme'),
        default=False,
        required=False,
    )

    scope_cooperation = schema.Bool(
        title=_(u'Scope of cooperation'),
        default=False,
        required=False,
    )


@grok.subscribe(IOffer, IObjectAddedEvent)
def numOfferDefaultValue(offer, event):
    registry = queryUtility(IRegistry)
    tfe_tool = registry.forInterface(ITfemarketSettings)
    center = tfe_tool.center_code
    total = tfe_tool.count_offers + 1

    offer.offer_id = str(center) + '-' + str(total).zfill(5)
    offer.reindexObject()

    tfe_tool.count_offers += 1
    transaction.commit()


@grok.subscribe(IOffer, IObjectModifiedEvent)
@grok.subscribe(IOffer, IObjectAddedEvent)
def defineTeacherAsEditor(offer, event):
    creator = getattr(offer.getOwner(), '_id', None)
    teacher = offer.teacher_manager

    for user in offer.get_local_roles():
        if user not in [creator, teacher]:
            offer.manage_delLocalRoles([user])

    offer.creators = tuple([creator, teacher])
    offer.manage_setLocalRoles(teacher, ["Owner"])
    offer.addCreator(teacher)
    offer.reindexObject()


class View(dexterity.DisplayForm):
    grok.require('zope2.View')
    grok.context(IOffer)
    grok.template('offer_view')

    def redirectToMarket(self):
        market_path = self.context.getParentNode().absolute_url()
        self.redirect(market_path + "?offer=" + self.context.offer_id)


class Add(dexterity.AddForm):
    grok.name('offer')

    def updateFields(self):
        super(Add, self).updateFields()
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        if not tfe_tool.view_num_students:
            self.fields = self.fields.omit('num_students')

    def updateWidgets(self):
        try:
            super(Add, self).updateWidgets()
        except ValueError as err:
            self.context.plone_utils.addPortalMessage(_("No esta correctament configurat: '%s'") % err, 'error')


@indexer(IOffer)
def offer_type(context):
    return context.offer_type


grok.global_adapter(offer_type, name='TFEoffer_type')


@indexer(IOffer)
def degree(context):
    return context.degree


grok.global_adapter(degree, name='TFEdegree')


@indexer(IOffer)
def teacher_manager(context):
    return context.teacher_manager


grok.global_adapter(teacher_manager, name='TFEteacher_manager')


@indexer(IOffer)
def dept(context):
    return context.dept


grok.global_adapter(dept, name='TFEdept')


@indexer(IOffer)
def company(context):
    return context.company


grok.global_adapter(company, name='TFEcompany')


@indexer(IOffer)
def grant(context):
    return context.grant


grok.global_adapter(grant, name='TFEgrant')


@indexer(IOffer)
def modality(context):
    return context.modality


grok.global_adapter(modality, name='TFEmodality')


@indexer(IOffer)
def keys(context):
    return context.keys


grok.global_adapter(keys, name='TFEkeys')


@indexer(IOffer)
def lang(context):
    return context.lang


grok.global_adapter(lang, name='TFElang')
