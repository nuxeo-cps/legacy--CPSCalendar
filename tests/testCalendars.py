import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSCalendarTestCase import CPSCalendarTestCase

from DateTime.DateTime import DateTime


class TestCalendarTool(CPSCalendarTestCase):

    def afterSetUp(self):
        self.user_id = 'root'
        self.login(self.user_id)

        # This actually creates an entry for root in portal_memberdata
        mtool = self.portal.portal_membership
        m = mtool.getAuthenticatedMember()
        m.setProperties(toto='toto')

        # If there is no entry for user, getCalendarForPath will return None
        dtool = self.portal.portal_metadirectories
        self.member = dtool.members.getEntry(self.user_id)
        assert self.member
        self.user_home = mtool.getHomeFolder(self.user_id)
        assert self.user_home
        self.user_home_url = mtool.getHomeUrl(self.user_id)
        assert self.user_home_url

    def beforeTearDown(self):
        self.logout()

    def testCalendarTool(self):
        caltool = self.portal.portal_cpscalendar
        assert(caltool)

        cal = caltool.getCalendarForPath(self.user_home_url)
        raise "DEBUG", str(self.user_home.absolute_path(relative=1))
        assert(cal)


class TestCalendar(CPSCalendarTestCase):

    def afterSetUp(self):
        self.user_id = 'root'
        self.login(self.user_id)

        # This actually creates an entry for root in portal_memberdata
        mtool = self.portal.portal_membership
        self.member = mtool.getAuthenticatedMember()

        member_home = mtool.getHomeFolder(self.user_id)
        assert member_home

        self.calendar = getattr(member_home, 'calendar')
        assert self.calendar


    def beforeTearDown(self):
        # portal_memberdata caches entries in a volatile variable that's
        # cleaned up upon request completion
        mdtool = self.portal.portal_memberdata
        del mdtool._v_temps

    def testDC(self):
        # XXX: the title should actually be more explicit than that.
        self.assertEquals(self.calendar.Title(), 
                          "cpscalendar_user_calendar_name_beg" \
                          + self.user_id \
                          + "cpscalendar_user_calendar_name_end")
        # XXX: there should be a description there.
        self.assertEquals(self.calendar.Description(), "")

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

        desc = self.calendar.getEventsDesc(
            start_time=DateTime(2003, 1, 1, 10, 0),
            end_time=DateTime(2003, 1, 1, 16, 0), disp='week')
        # XXX: add some test for desc here

        desc = self.calendar.getEventsDesc(
            start_time=DateTime(2003, 1, 1, 10, 0),
            end_time=DateTime(2003, 1, 1, 16, 0), disp='month')
        # XXX: add some test for desc here


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCalendarTool))
    suite.addTest(unittest.makeSuite(TestCalendar))
    return suite

