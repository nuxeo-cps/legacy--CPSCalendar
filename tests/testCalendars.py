import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSCalendarTestCase import CPSCalendarTestCase

from DateTime.DateTime import DateTime

MANAGER_FULLNAME="Manager CPS" #The default fullname for a CPS manager

class TestCalendarTool(CPSCalendarTestCase):

    def afterSetUp(self):
        self.login(self.user_id)

        # This actually creates an entry for root in portal_memberdata
        mtool = self.portal.portal_membership
        m = mtool.getAuthenticatedMember()
        # xxx = whatever here, what's important is to call setProperties()
        m.setProperties(xxx='xxx')

        # If there is no entry for user, getCalendarForPath will return None
        dtool = self.portal.portal_directories
        self.member = dtool.members.getEntry(self.user_id)
        assert self.member
        mtool.createMemberArea(self.user_id)
        self.user_home = mtool.getHomeFolder(self.user_id)
        user_workspace = getattr(self.portal.workspaces.members, self.user_id)
        self.assertEquals(self.user_home, user_workspace)
        assert self.user_home.calendar
        self.user_home_url = mtool.getHomeUrl(self.user_id)
        self.assertEquals(self.user_home_url,
            "http://nohost/portal/workspaces/members/%s" % self.user_id)

        self.caltool = self.portal.portal_cpscalendar
        assert self.caltool

    def beforeTearDown(self):
        mdtool = self.portal.portal_memberdata
        del mdtool._v_temps
        self.logout()

    def testCalendarTool(self):
        caltool = self.caltool

        self.assertEquals(caltool.getCalendarForPath('xxx'), None)

        rpath = 'workspaces/members/%s/calendar' % self.user_id
        self.assertEquals(caltool.getCalendarPathForUser(self.user_id), rpath)

        calendar = caltool.getCalendarForPath(rpath)
        self.assertEquals(calendar, self.user_home.calendar)

        calendar = caltool.getCalendarForUser(self.user_id)
        self.assertEquals(calendar, self.user_home.calendar)

        l = caltool.listCalendarPaths()
        l.sort()
        self.assertEquals(l, [
             'workspaces/members/%s/calendar' % self.user_id,
             'workspaces/members/test_user_1/calendar'])

        l = caltool.listCalendars()
        l = [calendar.getRpath() for calendar in l]
        l.sort()
        self.assertEquals(l, [
             'workspaces/members/%s/calendar' % self.user_id,
             'workspaces/members/test_user_1/calendar'])

        # XXX: test these later
        caltool.getCalendarsDict()

    def testListFreeSlots(self):
        self.assertEquals(self.caltool.listFreeSlots([]), [])
        free_slots = self.caltool.listFreeSlots([[[
            {'start': DateTime('2004/01/15'), 
             'stop': DateTime('2004/01/15')}, 
            {'start': DateTime('2004/01/15'), 
             'stop': DateTime('2004/01/16')}]]])
        self.assertEquals(free_slots, 
            [[{'start': DateTime('2004/01/15'), 
              'stop': DateTime('2004/01/16')}]])


    def testFreeBusy(self):
        assert self.caltool.getCalendarForPath(
            'workspaces/members/%s/calendar' % self.user_id)

        freebusy_info = self.caltool.getFreeBusy([], 
            DateTime('2004/01/15'), DateTime('2004/01/15'), 8, 0, 19, 0)
        self.assertEquals(freebusy_info['cal_users'], {})
        self.assertEquals(freebusy_info['slots'],
            [(DateTime('2004/01/15'), DateTime('2004/01/16'))])
        eventinfo = freebusy_info['hour_block_cols'][0][0][0][0]
        self.assertEquals(eventinfo['start'], DateTime('2004/01/15 08:00:00'))
        self.assertEquals(eventinfo['height'], (19-8)*60)
        event = eventinfo['event']
        self.assertEquals(event.from_date, DateTime('2004/01/15 08:00:00'))
        self.assertEquals(event.to_date, DateTime('2004/01/15 19:00:00'))

        freebusy_info = self.caltool.getFreeBusy(
            ['workspaces/members/%s/calendar' % self.user_id],
            DateTime('2004/01/15'), DateTime('2004/01/15'), 8, 0, 19, 0)
        self.assertEquals(freebusy_info['cal_users'],
            {'workspaces/members/%s/calendar' % self.user_id: MANAGER_FULLNAME})
        self.assertEquals(freebusy_info['slots'],
            [(DateTime('2004/01/15'), DateTime('2004/01/16'))])
        eventinfo = freebusy_info['hour_block_cols'][0][0][0][0]
        self.assertEquals(eventinfo['start'], DateTime('2004/01/15 08:00:00'))
        self.assertEquals(eventinfo['height'], (19-8)*60)
        event = eventinfo['event']
        self.assertEquals(event.from_date, DateTime('2004/01/15 08:00:00'))
        self.assertEquals(event.to_date, DateTime('2004/01/15 19:00:00'))
        # XXX make tests for calendars that actually have events.

class TestCalendar(CPSCalendarTestCase):

    def afterSetUp(self):
        self.login(self.user_id)

        # This actually creates an entry for root in portal_memberdata
        mtool = self.portal.portal_membership
        self.member = mtool.getAuthenticatedMember()
        mtool.createMemberArea(self.user_id)
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
        self.assertEquals(self.calendar.Title(), 
                          "cpscalendar_user_calendar_name_beg "
                          + MANAGER_FULLNAME +
                          " cpscalendar_user_calendar_name_end")
        self.assertEquals(self.calendar.Description(), "")

    def testGetOwnerId(self):
        self.assertEquals(self.calendar.getOwnerId(), self.user_id)

    def testEmptyCalendar(self):
        self.assertEquals(self.calendar.getPendingEventsCount(), 0)
        self.assertEquals(self.calendar.getPendingEvents(), ())

    def testAdditionalCalendars(self):
        self.assertEquals(self.calendar.getAdditionalCalendars(), ())
        self.calendar.setAdditionalCalendars(('test',))
        self.assertEquals(self.calendar.getAdditionalCalendars(), ('test',))

    def testGetEvents(self):
        calendar = self.calendar
        calendar.first_hour, calendar.last_hour = 0, 24
        start_time = DateTime(2003, 1, 1, 10, 0)
        end_time = DateTime(2003, 1, 1, 16, 0)

        events = calendar.getEvents(start_time, end_time)
        self.assertEquals(events, [])

        from_date = DateTime(2003, 1, 1, 12, 0)
        to_date = DateTime(2003, 1, 1, 14, 0)
        calendar.invokeFactory(
            'Event', 'event', from_date=from_date, to_date=to_date)
        event = self.calendar.event

        events = calendar.getEvents(start_time, end_time)
        self.assertEquals(events, [event])

        desc = calendar.getEventsDesc(
            start_time=start_time, end_time=end_time, disp='day')
        
        self.assertEquals(desc,
            {'hour_blocks': 
                [[[{'height': 720, 'event': None}]], 
                    [[{'height': 120, 'event': event, 'isdirty': 0}]]],
             'slots': [(start_time, end_time)], 
             'day_events': []})

        desc = calendar.getEventsDesc(
            start_time=DateTime(2003, 1, 1, 10, 0),
            end_time=DateTime(2003, 1, 1, 16, 0), disp='week')
        # XXX: add some test for desc here

        desc = calendar.getEventsDesc(
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
        self.assertEquals(event.getCalendarUser(), self.user_id)

        assert event.getEventDict() # Too complex to test
        self.assertEquals(event.getAttendeesDict(), 
            {'member': [
                {'status': 'confirmed', 
                 'usertype': 'member',
                 'rpath': 'workspaces/members/%s/calendar' % self.user_id, 
                 'id': self.user_id, 
                 'cn': MANAGER_FULLNAME}]})

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

        # assert somthing with event.getMyStatus()
        event.setMyStatus('decline')
        # assert somthing with event.getMyStatus()

    def testCancel1(self):
        self._addEvent()
        event = self.calendar.event

        event.setEventStatus('canceled')
        self.assertEquals(event.event_status, 'canceled')
        self.assert_(event.isdirty)
        self.assertEquals(self.calendar.getDeclinedCanceledEvents(),
                          {'canceled': ('event',), 'declined': ()})

    def testCancel2(self):
        self._addEvent()
        event = self.calendar.event

        event.cancelEvent(event)
        #self.assertEquals(event.event_status, 'canceled')
        self.assertEquals(self.calendar.getDeclinedCanceledEvents(),
                          {'canceled': ('event',), 'declined': ()})

        event.unCancelEvent(event)
        #self.assertEquals(event.event_status, 'canceled')
        self.assertEquals(self.calendar.getDeclinedCanceledEvents(),
                          {'canceled': (), 'declined': ()})

    def _testDecline1(self):
        self._addEvent()
        event = self.calendar.event

        event.setEventStatus('decline')
        self.assertEquals(event.event_status, 'decline')
        self.assert_(event.isdirty)
        self.assertEquals(self.calendar.getDeclinedCanceledEvents(),
                          {'canceled': (), 'declined': ('event',)})

    def testDecline2(self):
        self._addEvent()
        event = self.calendar.event

        self.calendar.declineEvent(event)
        #self.assertEquals(event.event_status, 'decline')
        self.assertEquals(self.calendar.getDeclinedCanceledEvents(),
                          {'canceled': (), 'declined': ('event',)})
        #self.calendar.unDeclineEvent(event)
        #self.assertEquals(event.event_status, 'XXX')
        #self.assertEquals(self.calendar.getDeclinedCanceledEvents(),
        #                  {'canceled': (), 'declined': ()})

    def testViewsWithEmptyCalendar(self):
        calendar = self.calendar
        self.portal.REQUEST.SESSION = {}
        assert calendar.calendar_view(disp="week")
        assert calendar.calendar_view(disp="month")
        assert calendar.calendar_view(disp="day")
        assert calendar.calendar_addevent_form()
        assert calendar.calendar_display_form()
        assert calendar.calendar_export()
        assert getattr(calendar, 'calendar.ics')()

    def testViewsWithOneEvent(self):
        self._addEvent()
        event = self.calendar.event
        calendar = self.calendar

        self.portal.REQUEST.SESSION = {}
        assert calendar.calendar_view(disp="week").count("xxyyzz")
        assert calendar.calendar_view(disp="month").count("xxyyzz")
        assert calendar.calendar_view(disp="day").count("xxyyzz")
        assert calendar.calendar_addevent_form()
        assert calendar.calendar_display_form()
        assert calendar.calendar_export()
        assert getattr(calendar, 'calendar.ics')().count("xxyyzz")

        self.portal.REQUEST['URL1'] = 'theurl'
        assert event.calendar_event_view()
        assert event.calendar_editevent_form()
        assert event.calendar_attendees_form()
        html = event.calendar_attendees_form(search_param='id_')
        #assert html.count(
        #    'value="workspaces/members/root/calendar">root</option>')

    def testMeeting(self):
        self._addEvent()
        event = self.calendar.event

        # No attendees so nothing should happen
        event.updateAttendeesCalendars()

        # TODO: add some real attendees
        mtool = self.portal.portal_membership
        mtool.createMemberArea('test_user_1')
        mdir = self.portal.portal_directories.members
        mdir.createEntry({'id': 'test_user_1', 
                          'email':'test_user_1@here.cps'})
        event.setAttendees([
            {'rpath': 'workspaces/members/test_user_1/calendar',
             'status': 'unconfirmed',
             'cn': 'test_user_1'}])
        event.updateAttendeesCalendars()
        # Try and decline it to see if notifications happen
        self.calendar.declineEvent(event)
        event.updateAttendeesCalendars()

    def testGetHourBlockCols(self):
        class DummyEvent:
            def isDirty(self):
                return 0
        calendar = self.calendar
        event = DummyEvent()

        hour_cols = [[]]
        hour_block_cols = calendar._getHourBlockCols(hour_cols, 1)
        self.assertEquals(hour_block_cols, [[]])

        hour_cols = [[
            {'event': event,
             'start': DateTime('2004/01/18 10:00:00'), 
             'stop': DateTime('2004/01/18 12:00:00')}]]
        hour_block_cols = calendar._getHourBlockCols(hour_cols, 1)
        self.assertEquals(len(hour_block_cols[0]), 2)
        empty_block = hour_block_cols[0][0][0][0]
        event_block = hour_block_cols[0][1][0][0]
        self.assertEquals(empty_block['height'], 2 * 60)
        self.assertEquals(event_block['height'], 2 * 60)

        hour_cols = [[
            {'event': event,
             'start': DateTime('2004/01/18 02:00:00'), 
             'stop': DateTime('2004/01/18 10:00:00')}]]
        hour_block_cols = calendar._getHourBlockCols(hour_cols, 1)
        self.assertEquals(len(hour_block_cols[0]), 1)
        event_block = hour_block_cols[0][0][0][0]
        self.assertEquals(event_block['height'], 2 * 60)

        hour_cols = [[
            {'event': event,
             'start': DateTime('2004/01/18 20:00:00'), 
             'stop': DateTime('2004/01/18 22:00:00')}]]
        hour_block_cols = calendar._getHourBlockCols(hour_cols, 1)
        self.assertEquals(hour_block_cols, [[]])

        hour_cols = [[
            {'event': event,
             'start': DateTime('2004/01/18 21:00:00'), 
             'stop': DateTime('2004/01/18 22:00:00')}]]
        hour_block_cols = calendar._getHourBlockCols(hour_cols, 1)
        self.assertEquals(hour_block_cols, [[]])

        hour_cols = [[
            {'event': event,
             'start': DateTime('2004/01/18 00:00:00'), 
             'stop': DateTime('2004/01/18 23:59:00')}]]
        hour_block_cols = calendar._getHourBlockCols(hour_cols, 1)
        self.assertEquals(len(hour_block_cols[0]), 1)
        event_block = hour_block_cols[0][0][0][0]
        self.assertEquals(event_block['height'], 
            (calendar.last_hour - calendar.first_hour) * 60)

        hour_cols = [
            [{'event': event,
              'start': DateTime('2004/01/18 10:00:00'), 
              'stop': DateTime('2004/01/18 14:00:00')}],
            [{'event': event,
              'start': DateTime('2004/01/18 9:00:00'), 
              'stop': DateTime('2004/01/18 12:00:00')}]]
        hour_block_cols = calendar._getHourBlockCols(hour_cols, 1)
        self.assertEquals(hour_block_cols,
            [[[[{'height': 120, 'event': None}]], 
              [[{'height': 240, 'event': event, 'isdirty': 0}]]], 
             [[[{'height': 60, 'event': None}]], 
              [[{'height': 180, 'event': event, 'isdirty': 0}]]]])

    def testEventDeletion(self):
        self._addEvent()
        event = self.calendar.event

        self.calendar.manage_delObjects(['event'])
        self.assert_(not hasattr(self.calendar, 'event'))
       

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCalendarTool))
    suite.addTest(unittest.makeSuite(TestCalendar))
    return suite

