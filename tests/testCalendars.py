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
        # xxx = whatever here, what's important is to call setProperties()
        m.setProperties(xxx='xxx')

        # If there is no entry for user, getCalendarForPath will return None
        dtool = self.portal.portal_metadirectories
        self.member = dtool.members.getEntry(self.user_id)
        assert self.member
        self.user_home = mtool.getHomeFolder(self.user_id)
        self.assertEquals(self.user_home, self.portal.workspaces.members.root)
        self.user_home_url = mtool.getHomeUrl(self.user_id)
        self.assertEquals(self.user_home_url, 
                          "http://nohost/portal/workspaces/members/root")
        self.caltool = self.portal.portal_cpscalendar
        assert self.caltool 

    def beforeTearDown(self):
        self.logout()

    def testCalendarTool(self):
        caltool = self.caltool

        # rpath is the path to "someplace"
        rpath = 'portal/workspaces/members/root'
        cal = caltool.getCalendarForPath(rpath)
        self.assertEquals(cal, self.user_home.calendar)
        cal = caltool.getCalendarForPath(rpath + '/calendar')
        self.assertEquals(cal, self.user_home.calendar)

        cal = caltool.getCalendarForUser('root')
        self.assertEquals(cal, self.user_home.calendar)

        l = caltool.listCalendarPaths()
        l.sort()
        self.assertEquals(l, [
             'portal/workspaces/members/root/calendar',
             'portal/workspaces/members/test_user_1_/calendar'])

        l = caltool.listCalendars()
        l = [cal.getRpath() for cal in l]
        l.sort()
        self.assertEquals(l, [
             'portal/workspaces/members/root/calendar',
             'portal/workspaces/members/test_user_1_/calendar'])

        # XXX: test these later
        assert caltool.listCalendarsDict()
        self.assertEquals(caltool.listFreeSlots([]), [])
        caltool.listFreeSlots(caltool.listCalendars())
        #assert caltool.getFreeBusy(...)


class TestCalendar(CPSCalendarTestCase):

    def afterSetUp(self):
        self.user_id = 'root'
        self.login(self.user_id)

        # This actually creates an entry for root in portal_memberdata
        mtool = self.portal.portal_membership
        self.member = mtool.getAuthenticatedMember()

        member_home = mtool.getHomeFolder(self.user_id)
        assert member_home
        self.calendar = member_home.calendar
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

    def testEventDesc(self):
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


    def _addEvent(self):
        # Create an event today so that it appears in the views for today
        now = DateTime()
        year, month, day = now.year(), now.month(), now.day()
        from_date = DateTime(year, month, day, 12, 0)
        to_date = DateTime(year, month, day, 14, 0)
        self.calendar.invokeFactory(
            'Event', 'event', title="xxyyzz", 
            from_date=from_date, to_date=to_date)

    def testAccessors(self):
        self._addEvent()
        event = self.calendar.event

        assert event.getOrganizerCalendar()
        self.assertEquals(event.getCalendar(), self.calendar)
        self.assertEquals(event.getCalendarUser(), 'root')

        assert event.getEventDict() # Too complex to test
        self.assertEquals(event.getAttendeesDict(), {})

    def testViews(self):
        self._addEvent()
        event = self.calendar.event

        # Test event's view and forms
        self.portal.REQUEST.SESSION = {}
        assert event.calendar_event_view()
        assert event.calendar_editevent_form()

    def testDecline(self):
        self._addEvent()
        event = self.calendar.event

        event.setMyStatus('decline')

    def testCancel(self):
        self._addEvent()
        event = self.calendar.event

        event.setEventStatus('canceled')
        self.assertEquals(event.event_status, 'canceled')
        self.assert_(event.isdirty)
        self.assertEquals(self.calendar.getDeclinedCanceledEvents(),
                          {'canceled': ('event',), 'declined': ()})

    def testViewsWithEmptyCalendar(self):
        self.portal.REQUEST.SESSION = {}
        assert self.calendar.calendar_view(disp="week")
        assert self.calendar.calendar_view(disp="month")
        assert self.calendar.calendar_view(disp="day")
        assert self.calendar.calendar_addevent_form()
        assert self.calendar.calendar_display_form()
        assert self.calendar.calendar_export()
        assert getattr(self.calendar, 'calendar.ics')()

    def testViewsWithOneEvent(self):
        self._addEvent()
        event = self.calendar.event

        self.portal.REQUEST.SESSION = {}
        assert self.calendar.calendar_view(disp="week").count("xxyyzz")
        assert self.calendar.calendar_view(disp="month").count("xxyyzz")
        assert self.calendar.calendar_view(disp="day").count("xxyyzz")
        assert self.calendar.calendar_addevent_form()
        assert self.calendar.calendar_display_form()
        assert self.calendar.calendar_export()
        assert getattr(self.calendar, 'calendar.ics')().count("xxyyzz")

    def testMeeting(self):
        self._addEvent()
        event = self.calendar.event

        # No attendees so nothing should happen
        event.updateAttendeesCalendars()

        # TODO: add some attendees

        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCalendarTool))
    suite.addTest(unittest.makeSuite(TestCalendar))
    return suite

