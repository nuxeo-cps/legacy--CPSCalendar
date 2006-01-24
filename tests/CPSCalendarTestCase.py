from Testing import ZopeTestCase
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from Products.CPSDefault.tests.CPSTestCase import CPSTestCase, MANAGER_ID

ZopeTestCase.installProduct('CPSCalendar')

class CPSCalendarTestCase(CPSTestCase):

    user_id = MANAGER_ID

    def afterSetUp(self):
        self.login(self.user_id)
        CPSTestCase.afterSetUp(self)
        if 'cps_calendar_installer' not in self.portal.objectIds():
            installer = ExternalMethod(
                'cps_calendar_installer',
                '',
                'CPSCalendar.install',
                'install')
            self.portal._setObject('cps_calendar_installer',
                                   installer)
        self.portal.cps_calendar_installer()

