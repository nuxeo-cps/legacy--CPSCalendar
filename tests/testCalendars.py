import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSCalendarTestCase import CPSCalendarTestCase

from DateTime.DateTime import DateTime


class TestCalendars(CPSCalendarTestCase):

    def afterSetUp(self):
        self.login('root')

    def beforeTearDown(self):
        self.logout()

    def testCalendars(self):
        calendars = self.portal.workspaces.calendars
        # XXX


class TestCalendar(CPSCalendarTestCase):

    def afterSetUp(self):
        self.login('root')

        # This actually creates an entry for root in portal_memberdata
        mtool = self.portal.portal_membership
        m = mtool.getAuthenticatedMember()
        m.setProperties(toto='toto')

        # If there is no entry for user, getCalendarForId will return None
        dtool = self.portal.portal_metadirectories
        members = dtool.members
        assert members.getEntry('root')

        calendars = self.portal.workspaces.calendars
        self.calendar = calendars.getCalendarForId('root')
        assert self.calendar

    def beforeTearDown(self):
        # portal_memberdata caches entries in a volatile variable that's
        # cleaned up upon request completion
        mdtool = self.portal.portal_memberdata
        del mdtool._v_temps

    def testEmptyCalendar(self):
        self.assertEquals(self.calendar.getPendingEventsCount(), 0)
        self.assertEquals(self.calendar.getPendingEvents(), ())

    def testAddOneEvent(self):
        from_date = DateTime(2003, 1, 1, 12, 0)
        to_date = DateTime(2003, 1, 1, 14, 0)
        self.calendar.invokeFactory(
            'Event', 'event', from_date=from_date, to_date=to_date)
        event = self.calendar.event

        start_time = DateTime(2003, 1, 1, 10, 0)
        end_time = DateTime(2003, 1, 1, 16, 0)
        desc = self.calendar.getEventsDesc(
            start_time=start_time, end_time=end_time, disp='day')
        self.assertEquals(desc,
            {'hour_blocks': 
                [[[{'height': 720, 'event': None}]], 
                    [[{'height': 120, 'event': event, 'isdirty': 0}]]],
             'slots': [(start_time, end_time)], 
             'day_events': []})

        xxx = self.calendar.getEventsDesc(
            start_time=DateTime(2003, 1, 1, 10, 0),
            end_time=DateTime(2003, 1, 1, 16, 0), disp='week')

        xxx = self.calendar.getEventsDesc(
            start_time=DateTime(2003, 1, 1, 10, 0),
            end_time=DateTime(2003, 1, 1, 16, 0), disp='month')



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCalendars))
    suite.addTest(unittest.makeSuite(TestCalendar))
    return suite

