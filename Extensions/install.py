# (c) 2003 Nuxeo SARL <http://nuxeo.com>
# $Id$
""" here we go
"""

from Products.CPSInstaller.CPSInstaller import CPSInstaller
from Products.CPSCore.CPSWorkflow import TRANSITION_INITIAL_CREATE
from Products.CPSCore.CPSWorkflow import TRANSITION_ALLOWSUB_CREATE
from Products.CPSCore.CPSWorkflow import TRANSITION_ALLOWSUB_DELETE
from Products.CPSCore.CPSWorkflow import TRANSITION_ALLOWSUB_MOVE
from Products.CPSCore.CPSWorkflow import TRANSITION_ALLOWSUB_COPY
from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent

WebDavLockItem = 'WebDAV Lock items'
WebDavUnlockItem = 'WebDAV Unlock items'

SKINS = {
   'cpscalendar_skins': 'Products/CPSCalendar/skins/cps_calendar',
   'cpscalendar_images': 'Products/CPSCalendar/skins/cps_calendar_images',
}

class CalendarInstaller(CPSInstaller):
    product_name = 'CPSCalendar'

    def install(self):
        self.log("Starting CPSCalendar install")
        self.verifySkins(SKINS)
        self.installTool()
        self.verifyAction(
                'portal_actions',
                id='my_calendar',
                name='My calendar',
                action='string:${portal/portal_cpscalendar/getHomeCalendarUrl}',
                condition="portal/portal_cpscalendar/getHomeCalendarObject",
                permission=(View,),
                category='user',
                visible=1)
        self.verifyAction(
                'portal_actions',
                id='create_my_calendar',
                name='Create my home calendar',
                action='string:${portal_url}/create_member_home_calendar',
                condition="python:portal.portal_membership.getHomeFolder() and \
                           not portal.portal_cpscalendar.getHomeCalendarObject() and \
                           getattr(portal.portal_cpscalendar, \
                                   'member_can_create_home_calendar', 1)",
                permission=(View,),
                category='user',
                visible=1)
        self.installPortalTypes()
        self.installWorkFlows()
        self.verifyTreeCacheTypes('workspaces', ('Calendar',), ('Calendar',))
        self.verifyMessageCatalog('cpscalendar', 'CPSCalendar messages')
        self.setupTranslations(message_catalog='cpscalendar')
        self.addPortalCatalogIndex('uid', 'FieldIndex')
        self.upgradeEvents()
        self.upgradeCalendars()
        self.log("End of specific CPSCalendar install")
        self.finalize()

    def installTool(self):
        # Install CPSCalendar Tool
        self.log("Verifying CPS Advanced Calendar tool")
        if not self.portalHas('portal_cpscalendar'):
            self.log(" Creating CPS Advanced Calendar tool")
            self.portal.manage_addProduct['CPSCalendar'].addCPSCalendarTool()

    def installPortalTypes(self):
        # Remove the old Event type, if it's a CMFCalendar event
        ttool = self.getTool('portal_types')
        if hasattr(ttool, 'Event'):
            if ttool['Event'].content_meta_type == 'CMF Event':
                ttool.manage_delObjects(['Event'])
            self.removeCalendarTypes(['Event'])
            
        # Temporary fix to force reinstall of types. This should be tested
        # to see if it's needed, or a isUserModified() should be called.
        ttool.manage_delObjects(['Event', 'Calendar'])

        ptypes = {'Calendar':{'allowed_content_types':('Event',),
                              'typeinfo_name':'CPSCalendar: Calendar',
                              'add_meta_type':'Factory-based Type Information',
                             },
                  'Event':   {'allowed_content_types':(),
                              'typeinfo_name':'CPSCalendar: Event',
                              'add_meta_type':'Factory-based Type Information',
                             },
                 }
        self.verifyContentTypes(ptypes)
        self.allowContentTypes('Calendar', 'Workspace')

    def installWorkFlows(self):
        wfdef = {'wfid': 'null_wf',
                 'permissions': (View, ModifyPortalContent,
                                 WebDavLockItem, WebDavUnlockItem,)
                 }

        wfstates = {
            'work': {
                'title': 'Work',
                'transitions':('subobject_actions',),
                'permissions': {View: ('Manager', 'WorkspaceManager',
                                       'WorkspaceMember', 'WorkspaceReader')},
            },
        }

        wftransitions = {
            'create': {
                'title': 'Initial creation',
                'new_state_id': 'work',
                'transition_behavior': (TRANSITION_INITIAL_CREATE,),
                'clone_allowed_transitions': None,
                'actbox_category': 'workflow',
                'props': {'guard_permissions':'',
                          'guard_roles':'Manager; WorkspaceManager; '
                                        'WorkspaceMember',
                          'guard_expr':''},
            },
            'subobject_actions': {
                'title': 'Initial creation',
                'new_state_id': 'work',
                'transition_behavior': (TRANSITION_ALLOWSUB_CREATE, 
                                        TRANSITION_ALLOWSUB_DELETE,
                                        TRANSITION_ALLOWSUB_MOVE,
                                        TRANSITION_ALLOWSUB_COPY,),
                'clone_allowed_transitions': None,
                'actbox_category': 'workflow',
                'props': {'guard_permissions':'',
                          'guard_roles':'Manager; WorkspaceManager; '
                                        'WorkspaceMember',
                          'guard_expr':''},
            },
        }
        self.verifyWorkflow(wfdef, wfstates, wftransitions, {}, {})
        
        wfs = {
            'Calendar': 'null_wf',
            'Event': 'null_wf',
        }
        self.verifyLocalWorkflowChains(self.portal['workspaces'], wfs)

    def upgradeEvents(self):
        # Get the events from the catalog:
        self.log("Upgrading events")
        events = self.portal.portal_catalog(portal_type='Event')
        for event in events:
            ob = event.getObject()
            res = ob.upgradeEventType()
            if res:
                self.log(res)
        self.log("  Done.")

    def upgradeCalendars(self):
        # Get the calendars from the catalog:
        self.log("Upgrading calendars")
        calendars = self.portal.portal_catalog(portal_type='Calendar')
        wftool = self.getTool('portal_workflow')
        wf = wftool['null_wf']
        tdef = wf.transitions.get('create', None)
        for calendar in calendars:
            ob = calendar.getObject()
            self.log(ob.absolute_url())
            res = ob.upgradePendingEvents()
            if res:
                self.log(res)
            res = wf._changeStateOf(ob, tdef, {})
            if res:
                self.log(res)
        self.log("  Done.")


def install(self):
    installer = CalendarInstaller(self)
    installer.install()
    return installer.logResult()

update = install #backwards compatibility
