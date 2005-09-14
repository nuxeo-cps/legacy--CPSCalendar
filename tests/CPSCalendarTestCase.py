from Testing import ZopeTestCase
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from Products.CPSDefault.tests import CPSTestCase

ZopeTestCase.installProduct('CPSCalendar')

class CPSCalendarTestCase(CPSTestCase.CPSTestCase):
    user_id = 'manager'

class CPSCalendarInstaller(CPSTestCase.CPSInstaller):

    def addPortal(self, id):

        # Install the CPS Portal
        CPSTestCase.CPSInstaller.addPortal(self, id)

        # Install the CNCCAuditFolders product
        portal = getattr(self.app, id)
        if 'cps_calendar_installer' not in portal.objectIds():
            installer = ExternalMethod(
                'cps_calendar_installer',
                '',
                'CPSCalendar.install',
                'install')
            portal._setObject('cps_calendar_installer',
                              installer)
        portal.cps_calendar_installer()

CPSTestCase.setupPortal(PortalInstaller=CPSCalendarInstaller)
    
