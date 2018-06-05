# -*- coding: utf-8 -*-

from five import grok
from plone.directives import dexterity
from plone.directives import form
from zope import schema

from genweb.tfemarket import _
from genweb.tfemarket.utils import checkPermissionCreateApplications
from genweb.tfemarket.z3cwidget import ReadOnlyInputFieldWidget
from genweb.tfemarket.z3cwidget import StudentInputFieldWidget


grok.templatedir("templates")


class IApplication(form.Schema):
    """ Application for an offer
    """

    form.widget('offer_id', ReadOnlyInputFieldWidget)
    offer_id = schema.TextLine(
        title=_(u'Offer id'),
        required=False,
    )

    form.widget('offer_title', ReadOnlyInputFieldWidget)
    offer_title = schema.TextLine(
        title=_(u'Offer title'),
        required=False,
    )

    form.widget('title', StudentInputFieldWidget)
    title = schema.TextLine(
        title=_(u'Fullname'),
        required=False,
    )

    form.widget('dni', ReadOnlyInputFieldWidget)
    dni = schema.TextLine(
        title=_(u'DNI'),
        required=False,
    )

    form.widget('prisma_id', ReadOnlyInputFieldWidget)
    prisma_id = schema.TextLine(
        title=_(u'PRISMA id'),
        required=False,
    )

    form.widget('email', ReadOnlyInputFieldWidget)
    email = schema.TextLine(
        title=_(u'Email'),
        required=False,
    )

    phone = schema.TextLine(
        title=_(u"Telephone"),
        required=False,
    )

    llista_expedients = schema.List(
        title=_(u'Codi Expedient'),
        value_type=(schema.Tuple(
                    value_type=schema.TextLine(),
                    max_length=2
                    )
                    ),
        required=False
    )

    body = schema.Text(
        title=_(u'Body'),
        required=False,
    )


class Add(dexterity.AddForm):
    grok.name('application')

    def getStudentData(self, name, value, pwd=None):
        import logging
        from Products.LDAPUserFolder.utils import to_utf8
        from Products.LDAPUserFolder.utils import guid2string
        from Products.LDAPUserFolder.LDAPDelegate import filter_format

        logger = logging.getLogger('event.LDAPUserFolder')
        student_data = {}
        return student_data

        users_base = self.users_base

        if name == 'dn':
            if value.find(',') == -1:
                # micro-optimization: this is not a valid dn because it
                # doesn't contain any commas; don't bother trying to look it
                # up
                msg = '_lookupuserbyattr: not a valid dn "%s"' % value
                logger.debug(msg)
                return None, None, None, None

            users_base = to_utf8(value)
            search_str = '(objectClass=*)'
        elif name == 'objectGUID':
            # we need to convert the GUID to a specially formatted string
            # for the query to work
            value = guid2string(value)
            # we can't escape the objectGUID query piece using filter_format
            # because it replaces backslashes, which we need as a result
            # of guid2string
            ob_flt = ['(%s=%s)' % (name, value)]
            search_str = self._getUserFilterString(filters=ob_flt)
        else:
            ob_flt = [filter_format('(%s=%s)', (name, value))]
            search_str = self._getUserFilterString(filters=ob_flt)

        # Step 1: Bind either as the Manager or anonymously to look
        #         up the user from the login given
        if self._binduid_usage > 0:
            bind_dn = self._binduid
            bind_pwd = self._bindpwd
        else:
            bind_dn = bind_pwd = ''

        # If you want to log the password as well, which can introduce
        # security problems, uncomment the next lines and comment out
        # the line after that, then restart Zope.
        # msg = '_lookupuserbyattr: Binding as "%s:%s"' % ( bind_dn
        #                                                , bind_pwd
        #                                                )
        logger.debug('_lookupuserbyattr: Binding as "%s"' % bind_dn)
        logger.debug('_lookupuserbyattr: Using filter "%s"' % search_str)

        known_attrs = self.getSchemaConfig().keys()

        res = self._delegate.search(base=users_base,
                                    scope=self.users_scope,
                                    filter=search_str,
                                    attrs=known_attrs,
                                    bind_dn=bind_dn,
                                    bind_pwd=bind_pwd
                                    )

        if res['size'] == 0 or res['exception']:
            msg = '_lookupuserbyattr: No user "%s=%s" (%s)' % (
                name, value, res['exception'] or 'n/a')
            logger.debug(msg)
            return None, None, None, None

        user_attrs = res['results'][0]
        dn = user_attrs.get('dn')
        utf8_dn = to_utf8(dn)

        if pwd is not None:
            # Step 2: Re-bind using the password passed in and the DN we
            #         looked up in Step 1. This will catch bad passwords.
            if self._binduid_usage != 1:
                user_dn = dn
                user_pwd = pwd
            else:
                user_dn = self._binduid
                user_pwd = self._bindpwd

                # Even though I am going to use the Manager DN and password
                # for the "final" lookup I *must* ensure that the password
                # is not a bad password. Since LDAP passwords
                # are one-way encoded I must ask the LDAP server to verify
                # the password, I cannot do it myself.
                try:
                    self._delegate.connect(bind_dn=utf8_dn, bind_pwd=pwd)
                except:
                    # Something went wrong, most likely bad credentials
                    msg = '_lookupuserbyattr: Binding as "%s" fails' % dn
                    logger.debug(msg)
                    return None, None, None, None

            logger.debug('_lookupuserbyattr: Re-binding as "%s"' % user_dn)

            auth_res = self._delegate.search(base=utf8_dn,
                                             scope=self._delegate.BASE,
                                             filter='(objectClass=*)',
                                             attrs=known_attrs,
                                             bind_dn=user_dn,
                                             bind_pwd=user_pwd
                                             )

            if auth_res['size'] == 0 or auth_res['exception']:
                msg = '_lookupuserbyattr: "%s" lookup fails bound as "%s"' % (
                    dn, user_dn)
                logger.debug(msg)
                return None, None, None, None

            user_attrs = auth_res['results'][0]

        else:
            user_pwd = pwd

        logger.debug('_lookupuserbyattr: user_attrs %s' % str(user_attrs))

        return dn, user_attrs

    def getStudentDegrees():
        degrees = []
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        return degrees

    def updateWidgets(self):
        super(Add, self).updateWidgets()
        if not checkPermissionCreateApplications(self, self.context):
            self.context.plone_utils.addPortalMessage(_(u"You have already created an application. You can see it on the main page of the market."), 'error')
            self.redirect(self.context.absolute_url())


class View(grok.View):
    grok.context(IApplication)
    grok.template('application_view')
