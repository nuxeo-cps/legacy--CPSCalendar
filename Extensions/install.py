# (c) 2003 Nuxeo SARL <http://nuxeo.com>
# $Id$
""" here we go
"""

import os
import sys
from random import randrange
from Acquisition import aq_base
from DateTime.DateTime import DateTime
from AccessControl import getSecurityManager
from App.Extensions import getPath
from zLOG import LOG, INFO, DEBUG
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression
from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent, \
     ReviewPortalContent, RequestReview

from Products.CPSCore.CPSWorkflow import \
     TRANSITION_INITIAL_PUBLISHING, TRANSITION_INITIAL_CREATE, \
     TRANSITION_ALLOWSUB_CREATE, TRANSITION_ALLOWSUB_PUBLISHING, \
     TRANSITION_BEHAVIOR_PUBLISHING, TRANSITION_BEHAVIOR_FREEZE
from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION
import Products.CPSCalendar

def groupcalendarinstall(self):
    _log = []
    def pr(bla, _log=_log):
        if bla == 'flush':
            return '\n'.join(_log)
        _log.append(bla)
        if (bla):
            LOG('cgroupcalendarinstall:', INFO, bla)

    def primp(pr=pr):
        pr(" !!! Can migrate that component !!!")

    def prok(pr=pr):
        pr(" Already correctly installed")

    portal = self.portal_url.getPortalObject()
    def portalhas(id, portal=portal):
        return id in portal.objectIds()

    pr("Starting install")
    pr("")
    installername = getSecurityManager().getUser().getUserName()
    pr("Current user: %s" % installername)

    # skins
    pr("Verifying skins")
    skins = ('cpscalendar',)
    paths = {
        'cpscalendar': 'Products/CPSCalendar/skins',
    }
    for skin in skins:
        path = paths[skin]
        path = path.replace('/', os.sep)
        pr(" FS Directory View '%s'" % skin)
        if skin in portal.portal_skins.objectIds():
            dv = portal.portal_skins[skin]
            oldpath = dv.getDirPath()
            if oldpath == path:
                prok()
            else:
                pr("  Correctly installed, correcting path")
                dv.manage_properties(dirpath=path)
        else:
            portal.portal_skins.manage_addProduct['CMFCore'].manage_addDirectoryView(filepath=path, id=skin)
            pr("  Creating skin")
    allskins = portal.portal_skins.getSkinPaths()
    for skin_name, skin_path in allskins:
        if skin_name != 'Basic':
            continue
        path = [x.strip() for x in skin_path.split(',')]
        path = [x for x in path if x not in skins] # strip all
        if path and path[0] == 'custom':
            path = path[:1] + list(skins) + path[1:]
        else:
            path = list(skins) + path
        npath = ', '.join(path)
        portal.portal_skins.addSkinSelection(skin_name, npath)
        pr(" Fixup of skin %s" % skin_name)
        
    # create workflow
    pr("Setup workflow shemas")
    wftool = portal.portal_workflow
    wfids = wftool.objectIds()

    # WF calendars
    wfid = 'calendar_folder_wf'
    pr(" Setup workflow %s" % wfid)
    if wfid in wfids:
        wftool.manage_delObjects([wfid])
    wftool.manage_addWorkflow(id=wfid,
                              workflow_type='cps_workflow (Web-configurable workflow for CPS)')
    wf = wftool[wfid]
    
    for s in ('work', ):
        wf.states.addState(s)
    for t in ('create', 'create_content', 'create_folder'):
        wf.transitions.addTransition(t)

    s = wf.states.get('work')
    s.setProperties(title='Work', 
                    transitions=('create_content',))
    t = wf.transitions.get('create')
    t.setProperties(title='Initial creation', new_state_id='work', 
                    transition_behavior=(TRANSITION_INITIAL_CREATE, ), 
                    clone_allowed_transitions=None,
                    actbox_name='', actbox_category='workflow', actbox_url='',
                    props={'guard_permissions':'', 
                           'guard_roles':'Manager; WorkspaceManager; WorkspaceMember', 
                           'guard_expr':''},
                    )
    t = wf.transitions.get('create_content')
    t.setProperties(title='Create content', new_state_id='work', 
                    transition_behavior=(TRANSITION_ALLOWSUB_CREATE, ), 
                    clone_allowed_transitions=None,
                    trigger_type=TRIGGER_USER_ACTION, 
                    actbox_name='New',
                    actbox_category='',
                    actbox_url='',
                    props={'guard_permissions':'', 
                           'guard_roles':'Manager; WorkspaceManager; WorkspaceMember', 
                           'guard_expr':''},
                    )

    # WF workspace content
    wfid = 'calendar_content_wf'
    pr(" Setup workflow %s" % wfid)
    if wfid in wfids:
        wftool.manage_delObjects([wfid])
    wftool.manage_addWorkflow(id=wfid,
                              workflow_type='cps_workflow (Web-configurable workflow for CPS)')
    wf = wftool[wfid]
    
    for s in ('work', ):
        wf.states.addState(s)
    for t in ('create', 'copy_submit', ):
        wf.transitions.addTransition(t)
    for v in ('action', 'actor', 'comments', 'review_history', 'time'):
        wf.variables.addVariable(v)
    for p in (View, ModifyPortalContent, ):
        wf.addManagedPermission(p)
        
    s = wf.states.get('work')
    s.setProperties(title='Work', 
                    transitions=('copy_submit',))
    s.setPermission(ModifyPortalContent, 0, ('Manager', 'WorkspaceManager', 'WorkspaceMember'))
    s.setPermission(View, 0, ('Manager', 'WorkspaceManager', 'WorkspaceMember', 'WorkspaceReader'))

    t = wf.transitions.get('create')
    t.setProperties(title='Initial creation', new_state_id='work', 
                    transition_behavior=(TRANSITION_INITIAL_CREATE, ),
                    clone_allowed_transitions=None,
                    actbox_name='', actbox_category='workflow', actbox_url='',
                    props={'guard_permissions':'',
                           'guard_roles':'Manager; WorkspaceManager; WorkspaceMember', 
                           'guard_expr':''},
                    )
    t = wf.transitions.get('copy_submit')
    t.setProperties(title='Copy content into a section for Publishing',
                    new_state_id='', 
                    transition_behavior=(TRANSITION_BEHAVIOR_PUBLISHING, ), 
                    clone_allowed_transitions=('submit', 'publish'),
                    trigger_type=TRIGGER_USER_ACTION, 
                    actbox_name='Submit', actbox_category='workflow',
                    actbox_url='%(content_url)s/content_submit_form',
                    props={'guard_permissions':'', 
                           'guard_roles':'Manager; WorkspaceManager; WorkspaceMember', 
                           'guard_expr':''},
                    )
    
    # wf variables
    wf.variables.setStateVar('review_state')
    vdef = wf.variables['action']
    vdef.setProperties(description='The last transition',
                       default_expr='transition/getId|nothing',
                       for_status=1, update_always=1)

    vdef = wf.variables['actor']
    vdef.setProperties(description='The ID of the user who performed '
                       'the last transition',
                       default_expr='user/getId',
                       for_status=1, update_always=1)

    vdef = wf.variables['comments']
    vdef.setProperties(description='Comments about the last transition',
                       default_expr="python:state_change.kwargs.get('comment', '')",
                       for_status=1, update_always=1)

    vdef = wf.variables['review_history']
    vdef.setProperties(description='Provides access to workflow history',
                       default_expr="state_change/getHistory",
                       props={'guard_permissions':'',
                              'guard_roles':'Manager; WorkspaceManager; WorkspaceMember; WorkspaceReader',
                              'guard_expr':''})

    vdef = wf.variables['time']
    vdef.setProperties(description='Time of the last transition',
                       default_expr="state_change/getDateTime",
                       for_status=1, update_always=1)


    # setup portal_type: CPS Proxy Document, CPS Proxy Folder
    # CPS Folder
    pr("Verifying portal types")
    ttool = portal.portal_types
    ptypes = {
        'CPSCalendar':('Calendars',
                       'Calendar',
                       'Event',
                      ),
        }
    allowed_content_type = {
                            'Calendars' : ('Calendar',),
                            'Calendar' : ('Event',),
                            'Event' : (),
                            }
    
    ptypes_installed = ttool.objectIds()
    
    for prod in ptypes.keys():
        for ptype in ptypes[prod]:
            pr("  Type '%s'" % ptype)
            if ptype in ptypes_installed:
                ttool.manage_delObjects([ptype])
                pr("   Deleted")

            ttool.manage_addTypeInformation(
                id=ptype,
                add_meta_type='Factory-based Type Information',
                typeinfo_name=prod+': '+ptype,
                )
            pr("   Installation")
    
    for ptype in ('Calendar', 'Event',):
        ttool[ptype].allowed_content_types = allowed_content_type[ptype]

    # check workflow association
    pr("Verifying workflow schemas")
    wfs = {
        'Calendar': 'calendar_folder_wf',
        }
    wftool = portal.portal_workflow
    pr("Installing workflow schemas")
    for pt, chain in wfs.items():
        wftool.setChainForPortalTypes([pt], chain)
    wftool.setDefaultChain('')

    # check site and calendars proxies
    calendars_id = 'Calendars'
    pr("Verifying roots: %s " % (calendars_id))
    if not portalhas(calendars_id):
        portal.portal_workflow.invokeFactoryFor(portal.this(), 'Calendars',
                                                calendars_id)
        portal[calendars_id].getContent().setTitle('Root of Calendars') # XXX L10N
        portal[calendars_id].reindexObject()
        pr("  Adding %s Folder" % calendars_id)
        
    pr("Verifying permissions")
    calendars_perm = {
        'Add portal content': ['Manager', 'WorkspaceManager', 'WorkspaceMember'],
        'Add portal folders': ['Manager', 'WorkspaceManager'],
        'Change permissions': ['Manager', 'WorkspaceManager'],
        'Delete objects': ['Manager', 'WorkspaceManager', 'WorkspaceMember'],
        'List folder contents': ['Manager', 'WorkspaceManager', 'WorkspaceMember', 'WorkspaceReader'],
        'Modify portal content': ['Manager', 'WorkspaceManager', 'WorkspaceMember'],
        'View': ['Manager', 'WorkspaceManager', 'WorkspaceMember', 'WorkspaceReader'],
        'View management screens': ['Manager', 'WorkspaceManager', 'WorkspaceMember'],
        }
    pr("Calendars")
    for perm, roles in calendars_perm.items():
        portal[calendars_id].manage_permission(perm, roles, 0)
        pr("  Permission %s" % perm)
    portal[calendars_id].reindexObjectSecurity()
    
    pr("Verifying local workflow association")
    if not '.cps_workflow_configuration' in portal[calendars_id].objectIds():
        pr("  Adding workflow configuration to %s" % calendars_id)
        portal[calendars_id].manage_addProduct['CPSCore'].addCPSWorkflowConfiguration()
        wfc = getattr(portal[calendars_id], '.cps_workflow_configuration')
        wfc.manage_addChain(portal_type='Calendar',
                            chain='calendar_folder_wf')
        wfc.manage_addChain(portal_type='Section',
                            chain='')
        wfc.manage_addChain(portal_type='Event',
                            chain='calendar_content_wf')

    # init Tree Tool
    trtool = portal.portal_trees
    pr("Verifying cache trees")
    if calendars_id not in trtool.objectIds():
        pr("  Adding cache for tree %s" % calendars_id)
        trtool.manage_addCPSTreeCache(id=calendars_id)
        trtool[calendars_id].manage_changeProperties(
            title=calendars_id+' Cache', 
            root=calendars_id, 
            type_names=('Calendar',),
            info_method='getFolderInfo')
        trtool[calendars_id].manage_rebuild()

    # i18n
    pr(" Adding i18n support")

    Localizer = portal['Localizer']
    # languages
    languages = Localizer.get_supported_languages()

    # MessageCatalog
    if 'cpscalendar' in Localizer.objectIds():
        Localizer.manage_delObjects(['cpscalendar'])
        pr("  previous default MessageCatalog deleted")
    Localizer.manage_addProduct['Localizer'].manage_addMessageCatalog(
        id='cpscalendar',
        title='CPSCalendar messages',
        languages=languages,
        )
    pr("  cpscalendar MessageCatalogCreated")
    defaultCatalog = Localizer.cpscalendar

    # computing po files' system directory
    product_path = sys.modules['Products.CPSCalendar'].__path__[0]
    i18n_path = os.path.join(product_path, 'i18n')
    pr("   po files are searched in %s" % i18n_path)
    pr("   po files for %s are expected" % str(languages))

    # loading po files
    for lang in languages:
        if lang == 'en':
            po_filename = 'locale.pot'
        else:
            po_filename = lang + '.po'
        pr("   importing %s file" % po_filename)
        po_path = os.path.join(i18n_path, po_filename)
        try:
            po_file = open(po_path)
        except NameError:
            pr("    %s file not found" % po_path)
        else:
            defaultCatalog.manage_import(lang, po_file)
            pr("    %s file imported" % po_path)


    # translation_service
    if portalhas('translation_service'):
        translation_service = portal.translation_service

        # translation domains
        translation_service.manage_setDomainInfo(path_0='Localizer/cpscalendar')
        pr("   cpscalendar domain set to Localizer/default")

        pr(" Reindexing catalog")
        portal.portal_catalog.refreshCatalog(clear=1)
    else:
        raise str('DependanceError'), 'translation_service'

    pr("Update Done")
    return pr('flush')
