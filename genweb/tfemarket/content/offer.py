# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from five import grok
from operator import itemgetter
from plone import api
from plone.autoform import directives
from plone.directives import dexterity, form
from plone.registry.interfaces import IRegistry
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.component import getMultiAdapter, queryUtility
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.security import checkPermission

from genweb.tfemarket import _
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.utils import checkOfferhasConfirmedApplications, getAllApplicationsFromOffer, getDegreeLiteralFromId, checkPermissionCreateApplications as CPCreateApplications
from genweb.tfemarket.validations import validateEmail
from genweb.tfemarket.z3cwidget import FieldsetFieldWidget, ReadOnlyInputFieldWidget, SelectModalityInputFieldWidget, TeacherInputFieldWidget

import transaction
import unicodedata


grok.templatedir("templates")


class LangsVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        results = ()
        languages = []

        langs = tfe_tool.languages
        if langs:
            results = langs.split("\r\n")

        for item in results:
            if isinstance(item, str):
                flattened = unicodedata.normalize('NFKD', item.decode(
                    'utf-8')).encode('ascii', errors='ignore')
            else:
                flattened = unicodedata.normalize('NFKD', item).encode('ascii', errors='ignore')
            languages.append(SimpleVocabulary.createTerm(item, flattened, item))

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


class DegreesVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        current_language = api.portal.get_current_language()

        result = []
        for item in tfe_tool.titulacions_table:
            titulacio = str(item['plan_year']) + " - "
            if current_language == 'ca':
                titulacio += item['titulacio_ca']
            elif current_language == 'es':
                titulacio += item['titulacio_es']
            else:
                titulacio += item['titulacio_en']

            result.append({'id': item['codi_prisma'], 'lit': titulacio})

        result = sorted(result, key=itemgetter('lit'))

        titulacions = []
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
        default=u"el centro",
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
        required=False,
    )

    topic = schema.Choice(
        title=_(u'offer_topic'),
        vocabulary=u"genweb.tfemarket.Topics",
        required=False
    )

    form.widget(degree=CheckBoxFieldWidget)
    degree = schema.List(
        value_type=schema.Choice(source=u"genweb.tfemarket.Titulacions"),
        title=_(u'degree'),
        required=False,
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

    observations = schema.TextLine(
        title=_(u'Observations'),
        required=False,
    )

    ############################################################################

    form.widget('fieldset_req', FieldsetFieldWidget)
    fieldset_req = schema.Text(
        default=_(u'Requirements'),
        required=False,
    )

    num_students = schema.Int(
        title=_(u'Number of students'),
        description=_(u'Number of students for the TFE (1 to 10)'),
        default=1,
        min=1,
        max=10,
        required=False,
    )

    workload = schema.Text(
        title=_(u'offer_workload'),
        required=False,
    )

    targets = schema.TextLine(
        title=_(u'offer_targets'),
        required=False,
    )

    features = schema.TextLine(
        title=_(u'offer_features'),
        required=False,
    )

    requirements = schema.TextLine(
        title=_(u'requirements'),
        required=False,
    )

    form.widget(lang=CheckBoxFieldWidget)
    lang = schema.List(
        value_type=schema.Choice(vocabulary=u"genweb.tfemarket.Langs"),
        title=_(u'tfe_lang'),
        required=False,
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

    ############################################################################

    form.widget('fieldset_opt', FieldsetFieldWidget)
    fieldset_opt = schema.Text(
        default=_(u'Options'),
        required=False,
    )

    grant = schema.Bool(
        title=_(u'grant'),
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


@grok.subscribe(IOffer, IObjectAddedEvent)
def defineTeacherAsEditor(offer, event):
    if offer.teacher_manager not in offer.creators:
        offer.creators += (offer.teacher_manager,)
        offer.manage_setLocalRoles(offer.teacher_manager, ["Owner"])
        offer.reindexObject()


class View(dexterity.DisplayForm):
    """The view. May will a template from <modulename>_templates/view.pt,
    and will be called 'view' unless otherwise stated.
    """
    grok.require('zope2.View')
    grok.context(IOffer)
    grok.template('offer_view')

    def formatDate(self, date):
        return date.strftime('%d/%m/%Y')

    def getDegreeLiteralFromId(self, id):
        return getDegreeLiteralFromId(id)

    def getRaw(self, raw):
        return raw.raw_encoded if hasattr(raw, 'raw_encoded') else None

    def getApplications(self):
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')
        results = []
        for item in getAllApplicationsFromOffer(self.context):
            application = item.getObject()
            workflowActions = wf_tool.listActionInfos(object=application)
            workflows = tools.workflow().getWorkflowsFor(application)[0]

            results.append(dict(title=item.Title,
                                state=workflows['states'][item.review_state].title,
                                url=item.getURL(),
                                item_path='/'.join(application.getPhysicalPath()[2:]),
                                dni=application.dni,
                                name=application.title,
                                email=application.email,
                                phone=application.phone,
                                offer_id=application.offer_id,
                                offer_title=application.offer_title,
                                workflows=workflowActions,
                                can_edit=checkPermission('cmf.ModifyPortalContent', application),
                                ))
        return results

    def checkPermissionCreateApplications(self):
        return CPCreateApplications(self, self.context)

    def showMessageAssignOffer(self):
        pw = getToolByName(self.context, "portal_workflow")
        offer_workflow = pw.getWorkflowsFor(self.context)[0].id
        offer_status = pw.getStatusOf(offer_workflow, self.context)
        if checkPermission('cmf.RequestReview', self) and checkOfferhasConfirmedApplications(self.context):
            if offer_status['review_state'] == 'intranet':
                return 'assignalofertaintranet'
            elif offer_status['review_state'] == 'public':
                return 'assign'
        return False

    def ifModalityCompany(self):
        return True if self.context.modality == 'Empresa' else False


class Add(dexterity.AddForm):
    grok.name('offer')

    def updateWidgets(self):
        super(Add, self).updateWidgets()
