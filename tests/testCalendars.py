import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSCalendarTestCase import CPSCalendarTestCase


class TestCalendars(CPSCalendarTestCase):

    def afterSetUp(self):
        self.login('root')

    def beforeTearDown(self):
        self.logout()

    def testCalendars(self):
        # Installer has created the calendars area
        calendars = self.portal.workspaces.calendars
        self.assert_(calendars)

        my_calendar = calendars.getCalendarForId('root')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCalendars))
    return suite

