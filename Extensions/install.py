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

def cpscalendarinstall(self):
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
        
##    pr("Setup workflow shemas")
    wftool = portal.portal_workflow
    trtool = portal.portal_trees


    # setup portal_type: CPS Proxy Document, CPS Proxy Folder
    # CPS Folder
    pr("Verifying portal types")
    ttool = portal.portal_types
    workspaceACT = list(ttool['Workspace'].allowed_content_types)
    if 'Calendars' not in  workspaceACT:
        workspaceACT.append('Calendars')
    if 'Calendar' not in  workspaceACT:
        workspaceACT.append('Calendar')
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
                            'Workspace' : workspaceACT
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
    
    for ptype in ('Workspace', 'Calendars', 'Calendar', 'Event',):
        ttool[ptype].allowed_content_types = allowed_content_type[ptype]

    # check workflow association
    pr("Verifying workflow schemas")
    wfs = {
        'Calendars': 'workspace_folder_wf',
        'Calendar': 'workspace_folder_wf',
        'Event': 'workspace_content_wf',
        }
    wftool = portal.portal_workflow
    pr("Installing workflow schemas")
    for pt, chain in wfs.items():
        wftool.setChainForPortalTypes([pt], chain)
    wftool.setDefaultChain('')

    # check site and workspaces
    workspace_id = 'calendars'
    calendars_id = 'members'
    pr("Verifying roots: %s and %s" % (calendars_id, workspace_id))
    if not portalhas(workspace_id):
        portal.portal_workflow.invokeFactoryFor(portal.this(), 'Workspace',
                                                workspace_id)
        portal[workspace_id].getContent().setTitle('Root of calendars workspace') # XXX L10N
        portal[workspace_id].reindexObject()
        pr("  Adding %s Folder" % workspace_id)
    pr("Verifying roots: %s " % (calendars_id))

    pr("Verifying permissions")
    workspaces_perm = {
        'Add portal content': ['Manager', 'WorkspaceManager', 'WorkspaceMember'],
        'Add portal folders': ['Manager', 'WorkspaceManager'],
        'Change permissions': ['Manager', 'WorkspaceManager'],
        'Delete objects': ['Manager', 'WorkspaceManager', 'WorkspaceMember'],
        'List folder contents': ['Manager', 'WorkspaceManager', 'WorkspaceMember', 'WorkspaceReader'],
        'Modify portal content': ['Manager', 'WorkspaceManager', 'WorkspaceMember'],
        'View': ['Manager', 'WorkspaceManager', 'WorkspaceMember', 'WorkspaceReader'],
        'View management screens': ['Manager', 'WorkspaceManager', 'WorkspaceMember'],
        }

    pr("Calendar workspace")
    for perm, roles in workspaces_perm.items():
        portal[workspace_id].manage_permission(perm, roles, 0)
        pr("  Permission %s" % perm)
    portal[workspace_id].reindexObjectSecurity()
    
    pr("Verifying local workflow association")
    if not '.cps_workflow_configuration' in portal[workspace_id].objectIds():
        pr("  Adding workflow configuration to %s" % workspace_id)
        portal[workspace_id].manage_addProduct['CPSCore'].addCPSWorkflowConfiguration()
        wfc = getattr(portal[workspace_id], '.cps_workflow_configuration')
        wfc.manage_addChain(portal_type='Workspace',
                            chain='workspace_folder_wf')
        wfc.manage_addChain(portal_type='Event',
                            chain='workspace_content_wf')
        wfc.manage_addChain(portal_type='Calendars',
                            chain='workspace_folder_wf')
        wfc.manage_addChain(portal_type='Calendar',
                            chain='workspace_folder_wf')

    # init Tree Tool
    if workspace_id not in trtool.objectIds():
        pr("  Adding cache for tree %s" % workspace_id)
        trtool.manage_addCPSTreeCache(id=workspace_id)
        trtool[workspace_id].manage_changeProperties(
            title=workspace_id+' Cache', 
            root=workspace_id, 
            type_names=('Workspace',),
            info_method='getFolderInfo')
    trtool[workspace_id].manage_rebuild()
    pr("   Workspaces cache rebuilded")
    
    # check site and calendars proxies
    if calendars_id not in portal[workspace_id].objectIds():
        portal[workspace_id].portal_workflow.invokeFactoryFor(portal[workspace_id].this(), 'Calendars',
                                                calendars_id)
        portal[workspace_id].members.getContent().setTitle('Root of members calendars') # XXX L10N
        portal[workspace_id].members.reindexObject()
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
        portal[workspace_id].members.manage_permission(perm, roles, 0)
        pr("  Permission %s" % perm)
    portal[workspace_id].members.reindexObjectSecurity()

    # init Tree Tool
    pr("Verifying cache trees")
    pr("   Sections cache rebuilded")
    if calendars_id not in trtool.objectIds():
        pr("  Adding cache for tree %s" % calendars_id)
        trtool.manage_addCPSTreeCache(id=calendars_id)
        trtool[calendars_id].manage_changeProperties(
            title=calendars_id+' Cache', 
            root=calendars_id, 
            type_names=('Calendars',),
            info_method='getFolderInfo')
        trtool[calendars_id].manage_rebuild()

    # i18n
    pr(" Adding i18n support")
    calendar_catalog_id='cpscalendar'

    Localizer = portal['Localizer']
    # languages
    languages = Localizer.get_supported_languages()

    # MessageCatalog
    if calendar_catalog_id in Localizer.objectIds():
        Localizer.manage_delObjects([calendar_catalog_id])
        pr("  previous default MessageCatalog deleted")
    Localizer.manage_addProduct['Localizer'].manage_addMessageCatalog(
        id=calendar_catalog_id,
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
            pr("  before  %s file imported" % po_path)
            defaultCatalog.manage_import(lang, po_file)
            pr("    %s file imported" % po_path)


    # translation_service
    if portalhas('translation_service'):
        translation_service = portal.translation_service

        if not portal['translation_service'].cpscalendar:
            # translation domains
            translation_service.manage_addDomainInfo(calendar_catalog_id,
                                                     'Localizer/'+calendar_catalog_id)
            pr("   cpscalendar domain set to Localizer/cpscalendar")

        pr(" Reindexing catalog")
        portal.portal_catalog.refreshCatalog(clear=1)
    else:
        raise str('DependanceError'), 'translation_service'

    pr("Update Done")
    return pr('flush')
