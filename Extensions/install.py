# (c) 2003 Nuxeo SARL <http://nuxeo.com>
# $Id$
""" here we go
"""

import os, sys
from zLOG import LOG, INFO, DEBUG

import Products.CPSCalendar

from Products.CPSDefault.Installer import BaseInstaller

SKINS = (
   ('cpscalendar_skins', 'Products/CPSCalendar/skins/cps_calendar'),
   ('cpscalendar_images', 'Products/CPSCalendar/skins/cps_calendar_images'),
)

class CPSInstaller(BaseInstaller):
    product_name = 'CPSCalendar'

    def install(self):
        self.log("Starting CPSCalendar install")
        self.setupSkins(SKINS)
        self.installTool()
        self.log(oldUpdate(self.portal))
        self.addUidIndex()
        self.log("End of specific CPSCalendar install")

    def installTool(self):
        # Install CPSCalendar Tool
        self.log("Verifying CPS Advanced Calendar tool")
        if not self.portalHas('portal_cpscalendar'):
            self.log(" Creating CPS Advanced Calendar tool")
            self.portal.manage_addProduct['CPSCalendar'].addCPSCalendarTool()

    # XXX: make this more generic later
    def addUidIndex(self):
        ct = self.portal.portal_catalog
        try:
            ct.delIndex('uid')
        except:
            pass
        ct.addIndex('uid', 'FieldIndex')
        ct.manage_reindexIndex(ids=['uid'])


def update(self):
    installer = CPSInstaller(self)
    installer.install()
    return installer.logResult()


# XXX: refactor the rest later
def oldUpdate(self):
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

    workspaces_id = 'workspaces'


    # Verification of the action and addinf if neccesarly 
    action_found = 0
    for action in portal['portal_actions'].listActions():
        if action.id == 'my_calendar':
            action_found = 1

    if not action_found:
        portal['portal_actions'].addAction(
            id='my_calendar',
            name='My calendar',
            action='string:${portal/portal_membership/getHomeUrl}/calendar',
            condition='python:portal.portal_membership.getHomeUrl()',
            permission=('View',),
            category='user',
            visible=1)
        pr(" Added Action My calendar")
    else:
        pass

    # setup portal_type: CPS Proxy Document, CPS Proxy Folder
    # CPS Folder
    pr("Verifying portal types")
    ttool = portal.portal_types
    workspaceACT = list(ttool['Workspace'].allowed_content_types)
    for ptype in ('Calendar',):
        if ptype not in  workspaceACT:
            workspaceACT.append(ptype)

    ptypes = {
        'CPSCalendar': (
            'Calendar',
            'Event',
        ),
    }

    allowed_content_type = {
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
    
    for ptype in allowed_content_type.keys():
        ttool[ptype].allowed_content_types = allowed_content_type[ptype]

    # check workflow association
    pr("Setup workflow shemas")
    wftool = portal.portal_workflow
    wfs = {
        'Calendar': 'workspace_folder_wf',
        'Event': 'workspace_content_wf',
    }

    pr("Installing workflow schemas")
    wfc = getattr(portal[workspaces_id], '.cps_workflow_configuration')
    for portal_type, chain in wfs.items():
        wfc.manage_addChain(portal_type=portal_type, chain=chain)

    # We need it to collaborative job
    pr("=> Update portal_trees cache")
    trtool = portal.portal_trees
    pr(repr(trtool[workspaces_id].type_names))
    pr(repr(trtool[workspaces_id].meta_types))
    WTN = list(trtool[workspaces_id].type_names)
    for type_name in ('Calendar',):
        if type_name not in WTN:
            WTN.append(type_name)
    trtool[workspaces_id].type_names = WTN
    
    WMT = list(trtool[workspaces_id].meta_types)
    for type_name in ('Calendar',):
        if type_name not in WMT:
            WMT.append(type_name)
    trtool[workspaces_id].meta_types = WMT
    
    trtool[workspaces_id].manage_rebuild()

    # i18n
    pr(" Adding i18n support")
    calendar_catalog_id = 'cpscalendar'

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
        po_filename = lang + '.po'
        pr("   importing %s file" % po_filename)
        po_path = os.path.join(i18n_path, po_filename)
        try:
            po_file = open(po_path)
        except (IOError, NameError):
            pr("    %s file not found" % po_path)
        else:
            pr("  before  %s file imported" % po_path)
            defaultCatalog.manage_import(lang, po_file)
            pr("    %s file imported" % po_path)


    # translation_service
    if portalhas('translation_service'):
        translation_service = portal.translation_service

        try:
            if getattr(translation_service, calendar_catalog_id, None) == None:
                translation_service.manage_addDomainInfo(calendar_catalog_id,
                                                         'Localizer/'+calendar_catalog_id)
        except:
            pass
        pr("   cpscalendar domain set to Localizer/cpscalendar")

        pr(" Reindexing catalog")
        portal.portal_catalog.refreshCatalog(clear=1)
    else:
        raise 'Dependance Error', 'translation_service'

    pr("Update Done")
    return pr('flush')
