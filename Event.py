# Copyright (c) 2002-2004 Nuxeo SARL <http://nuxeo.com>
# Copyright (c) 2002 CIRB, Belgique
# Authors: Julien Jalon <mailto:jj@nuxeo.com>
#          Lennart Regebro <mailto:lr@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$

"""
  Event
"""

from copy import deepcopy

from zLOG import LOG, DEBUG, INFO
from DateTime import DateTime
from Acquisition import aq_parent, aq_inner, aq_base
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName

from Products.CPSCore.CPSBase import CPSBaseDocument


factory_type_information = (
    {'id': 'Event',
     'title': 'portal_type_Calendar_Event_title',
     'description': 'portal_type_Calendar_Event_description',
     'content_icon': 'event_icon.gif',
     'product': 'CPSCalendar',
     'factory': 'addEvent',
     'meta_type': 'Event',
     'immediate_view': 'event_edit_form',
     'allow_discussion': 0,
     'filter_content_types': 0,
     'actions': ({'id': 'view',
                  'name': 'action_view',
                  'action': 'string:${object_url}/calendar_event_view',
                  'condition': '',
                  'permissions': (View,)},
                 {'id': 'edit',
                  'name': 'action_modify',
                  'action': 'string:${object_url}/calendar_editevent_form',
                  'condition': 'python:object.getCalendar() == object.getOrganizerCalendar()',
                  'permissions': (ModifyPortalContent,)},
                 {'id': 'attendees',
                  'name': 'action_attendees',
                  'action': 'string:${object_url}/calendar_attendees_form',
                  'condition': 'python:object.getCalendar() == object.getOrganizerCalendar()',
                  'permissions': (ModifyPortalContent,)},
                 {'id': 'delete',
                  'name': 'button_cancel',
                  'action': 'string:${object_url}/calendar_delevent',
                  'condition': 'python:object.getCalendar() == object.getOrganizerCalendar()',
                  'permissions': (ModifyPortalContent,)},
                 {'id': 'calendar',
                  'name': 'action_calendar',
                  'action': 'string:${object_url}/../',
                  'permissions': (View,)},
                 {'id': 'create',
                  'name': 'action_create',
                  'action': 'string:${object_url}/calendar_eventcreate_form',
                  'condition': '',
                  'visible': 0,
                  'permissions': ()},
                )
     },
    )


class Event(CPSBaseDocument):
    """
    Event
    """
    meta_type = 'Event'

    security = ClassSecurityInfo()
    display_type = 'standard_event'

    _properties = CPSBaseDocument._properties + (
        {'id': 'transparent', 'type': 'boolean', 'mode': 'w',
         'label': 'Transparent Event'},
        {'id': 'location', 'type': 'text', 'mode': 'w', 'label': 'Location'},
        {'id': 'event_status', 'type': 'text', 'mode': 'w',
         'label': 'Event Status'},
        {'id': 'category', 'type': 'text', 'mode': 'w', 'label': 'Category'},
        {'id': 'event_type', 'type': 'selection', 'mode': 'w',
         'label': 'Event Type', 'select_variable': 'event_types' },
        {'id': 'recurrence_period', 'type': 'selection', 'mode': 'w',
         'label': 'Recurrence Period', 'select_variable': 'period_types' },
        {'id': 'document', 'type': 'text', 'mode': 'w',
         'label': 'Document Link',},
    )

    #
    # Content accessors
    #

    organizer = {}
    attendees = ()
    from_date = None
    to_date = None
    location = ''
    event_status = 'unconfirmed'
    category = ''
    transparent = 0
    # Marks that an upgrade from the older 'all_day' attribute is needed
    event_type = None
    recurrence_period = 'period_daily'
    event_types = [ 'event_tofrom',     # To a time from a time
                    'event_allday',     # From a date to a date
                    'event_recurring']  # Repeats
    period_types = ['period_daily',
                    'period_weekly',
                    'period_monthly',
                    'period_quarterly', # Every three months
                    'period_yearly',
                    ]

    isdirty = 1
    notified_attendees = ()
    document = ''

    def __init__(self, id, organizer={}, attendees=(),
                 from_date=None, to_date=None, document='', **kw):
        LOG('CPSCalendar', DEBUG, "__init__ kw = ", kw)
        CPSBaseDocument.__init__(self, id, organizer=organizer, **kw)
        self.organizer = deepcopy(organizer)
        if attendees is not None:
            add_organizer = 1
            for each in attendees:
                if each['rpath'] == organizer['rpath']:
                    add_organizer = 0
                    break
            if add_organizer:
                orgdict = deepcopy(organizer)
                orgdict['status'] = 'confirmed'
                attendees = attendees + [orgdict]
            self.setAttendees(attendees)
        self.from_date = from_date 
        self.to_date = to_date
        self.event_type = kw.get('event_type', 'event_tofrom')
        self.location = kw.get('location')
        self.event_status = kw.get('event_status')
        self.category = kw.get('category')
        self.transparent = kw.get('transparent')
        self.recurrence_period = kw.get('recurrence_period', 'period_daily')
        self.document = document
        self._normalize()
        # It should never be dirty after creation, but some of the
        # above methods may set it to dirty.
        self.isdirty = 0

    security.declareProtected('Modify portal content', 'edit')
    def edit(self, from_date=None, to_date=None,
             event_type=None, transparent=None, document=None, **kw):
        """Edit method"""
        if self._edit(from_date, to_date,
             event_type, transparent, document, **kw):
            self.isdirty = 1
            self.notified_attendees = ()
        
    def _edit(self, from_date=None, to_date=None,
             event_type=None, transparent=None, document=None, **kw):
        """Edits an event and returns 1 if there was any changes"""
        setdirty = 0
        old_status = self.event_status
        CPSBaseDocument.edit(self, **kw)
        new_status = self.event_status
        if new_status != old_status:
            if new_status == 'canceled':
                calendar = self.getCalendar()
                calendar.cancelEvent(self)
            if old_status == 'canceled':
                calendar = self.getCalendar()
                calendar.unCancelEvent(self)
            setdirty = 1

        if event_type is not None and event_type != self.event_type:
            setdirty = 1
            self.event_type = event_type
        if transparent is not None:
            self.transparent = transparent
        if from_date is not None and self.from_date != from_date:
            setdirty = 1
            self.from_date = from_date
        if to_date is not None and self.to_date != to_date:
            setdirty = 1
            self.to_date = to_date
        if document is not None and document != self.document:
            setdirty = 1
            self.document = document
        self._normalize()
        return setdirty

    def upgradeEventType(self, REQUEST=None):
        """Upgrades properties"""
        # Return a string if upgrading even if there is no request, 
        # for use in logging when running the install.
        msg = []
               
        if self.event_type is None:
            if self.all_day:
                self.event_type = 'event_allday'
            else:
                self.event_type = 'event_tofrom'
                msg.append("%s upgraded to %s" % (self.absolute_url(),
                                                  self.event_type))
        elif hasattr(aq_base(self), 'recurrance_period'):
            # Upgrade from earlier bad spelling
            try:
                self.recurrence_period = self.recurrance_period[:]
            except TypeError:
                # version before 1.0, do not upgrade
                pass
            delattr(self, 'recurrance_period')
            msg.append("%s upgraded to 1.6.4" % self.absolute_url())
        
        attendee_upgrade = 0
        new_attendees = []
        for attendee in self.attendees:
            if attendee.get('id') == 'calendar':
                attendee['id'] = attendee['rpath'].split('/')[-2]
                attendee_upgrade = 1
            new_attendees.append(attendee)
                
        if attendee_upgrade:
            self.attendees = new_attendees
            msg.append("%s upgraded to 1.6.2" % self.absolute_url())
    
        if msg:
            return '\n'.join(msg)
        if REQUEST is not None:
            return "No upgrade needed"

    def _normalize(self):
        """Normalize from_date and to_date attributes"""
        if self.event_type == 'event_allday':
            from_date = self.from_date
            if from_date is not None:
                time_since_daystart = from_date.hour() * 3600 \
                    + from_date.minute() * 60 + from_date.second()
                if time_since_daystart:
                    timeTime = from_date.timeTime()
                    self.from_date = DateTime(timeTime - time_since_daystart)
            to_date = self.to_date
            if to_date is not None:
                time_since_daystart = to_date.hour() * 3600 \
                    + to_date.minute() * 60 + to_date.second()
                # 86399 sec = 24h - 1sec
                if time_since_daystart != 86399:
                    timeTime = to_date.timeTime()
                    self.to_date = DateTime(
                        timeTime - time_since_daystart + 86399)
        if self.to_date.lessThan(self.from_date):
            to_date = self.to_date
            self.to_date = self.from_date
            self.from_date = to_date

            if self.event_type == 'event_allday':
                self._normalize()

    security.declareProtected(View, 'SearchableText')
    def SearchableText(self):
        """Used by the catalog for basic full text indexing."""
        ctool = getToolByName(self, 'portal_cpscalendar')
        if ctool.event_fulltext_index:
            return '%s %s' % (self.title, self.description)
        return ''

    security.declareProtected(View, 'getCalendar')
    def getCalendar(self):
        """Return the calendar where this event is in"""
        return aq_parent(aq_inner(self))

    # FIXME
    security.declareProtected(View, 'getCalendarUser')
    def getCalendarUser(self):
        """Return the id of the calendar instead of the user"""
        # XXX: we assume that calendar are directly stored on the
        # user's workspace
        return aq_parent(self.getCalendar()).getOwner(1)[1]

    security.declareProtected(View, 'getOrganizerCalendar')
    def getOrganizerCalendar(self):
        """Return the calendar of the organizer of the event"""
        ctool = getToolByName(self, 'portal_cpscalendar')
        org_calendar = ctool.getCalendarForPath(
            self.organizer['rpath'], unrestricted=1)
        return org_calendar

    security.declareProtected(View, 'getAttendeesDict')
    def getAttendeesDict(self):
        """Return the attendees of the event"""
        attendees_dict = {}
        for attendee in self.attendees:
            entry = attendees_dict.setdefault(attendee['usertype'], [])
            entry.append(deepcopy(attendee))
        return attendees_dict

    security.declareProtected('Add portal content', 'getPendingEvents')
    def getPendingEvents(self):
        """Return pending events of this event's calendar"""
        return self.getCalendar().getPendingEvents(event_id=self.id)

    security.declareProtected(View, 'getEventDict')
    def getEventDict(self, comment=''):
        """
        """
        (member, member_cn, dtstamp) = self._getRequestInformations()
        return {
            'id': self.id,
            'request': 'request',
            'event': {
                'id': self.id,
                'organizer': deepcopy(self.organizer),
                'attendees': deepcopy(self.attendees),
                'from_date': self.from_date,
                'to_date': self.to_date,
                'category': self.category,
                'event_type': self.event_type,
                'title': self.title,
                'description': self.description,
                'location': self.location,
                'event_status': self.event_status,
                'transparent': self.transparent,
                'comment': comment,
                'dtstamp': dtstamp,
                'sender': member,
                'sender_cn': member_cn,
            }
        }

    security.declareProtected('View', 'canEditThisEvent')
    def canEditThisEvent(self):
        """Return True if we are allowed to modify"""
        user = self.REQUEST.get('AUTHENTICATED_USER')
        if user is None:
            return 0
        if user.getId() != self.getCalendarUser() and \
           self.to_date < DateTime():
            return 0
        return user.has_permission('Modify portal content', self)
        
    security.declareProtected('Add portal content', 'isDirty')
    def isDirty(self):
        """Check if we can edit the event"""
        return not not ((self.isdirty and self.attendees and
            self.canEditThisEvent()) or self.getPendingEvents())

    security.declareProtected('Add portal content', 'setEventStatus')
    def setEventStatus(self, status):
        """ 
        """

        # Only called with status = 'canceled', it seems -> refactor later
        assert status == 'canceled'
        old_status = self.event_status
        if status != old_status:
            if status == 'canceled':
                calendar = self.getCalendar()
                calendar.cancelEvent(self)
            if old_status == 'canceled':
                calendar = self.getCalendar()
                calendar.unCancelEvent(self)
            self.notified_attendees = ()
            self.isdirty = 1
        self.event_status = status

    security.declareProtected('Add portal content', 'setAttendees')
    def setAttendees(self, attendees):
        """Set atendees of the event from a attendees dictionary"""
        self.attendees = deepcopy(attendees)
        all_rpaths = tuple([attendee['rpath'] for attendee in attendees])
        self.notified_attendees = tuple(
            [rpath for rpath in self.notified_attendees
                   if rpath in all_rpaths])
        self.isdirty = self.notified_attendees != all_rpaths

    def removeAttendees(self, attendees):
        """Removes attendees from attendee-list"""
        self._removeAttendees(attendees)
        
        ctool = getToolByName(self, 'portal_cpscalendar')
        for attendee in self.attendees:
            apath = attendee['rpath']
            acal = ctool.getCalendarForPath(apath, unrestricted=1)
            event = acal._getOb(self.getId(), None)
            if event is not None:
                event._removeAttendees(attendees)
            
            # Check pending events
            for event in acal._pending_events:
                if event['id'] != event_id:
                    continue
                for att in event['event']['attendees']:
                    if att['rpath'] in attendees:
                        event['event']['attendees'].remove(att)
                        acal._p_changed = 1

        
    def _removeAttendees(self, attendees):
        """Removes attendees from attendee-list"""
        event_dict = self.getEventDict()
        event_dict['event']['event_status'] = 'canceled'
        self.updateAttendeesCalendars(attendees=attendees,
            event_dict=event_dict)
        for attendee in self.attendees:
            if attendee['rpath'] in attendees:
                self.attendees.remove(attendee)
        self._p_changed = 1
        
    security.declareProtected('Add portal content', 'setAttendeeStatus')
    def setAttendeeStatus(self, changed_attendee, status):
        """Set the attendee's status"""
        change = 0
        for attendee in self.attendees:
            if attendee['rpath'] == changed_attendee:
                attendee['status'] = status
                change = 1
        if change:
            self._p_changed = 1

    security.declareProtected('View', 'getMyStatus')
    def getMyStatus(self):
        """Return the status of the current calendar for this event"""
        my_rpath = self.getCalendar().getRpath()
        for attendee in self.attendees:
            if attendee['rpath'] == my_rpath:
                return attendee['status']

    security.declareProtected('Add portal content', 'setMyStatus')
    def setMyStatus(self, status, comment='', REQUEST=None):
        """Set the status for the current calendar"""
        calendar = self.getCalendar()
        calendar_rpath = calendar.getRpath()
        event_id = self.getId()
        (member, member_cn, dtstamp) = self._getRequestInformations()
        for attendee in self.attendees:
            if attendee['rpath'] == calendar_rpath:
                old_status = attendee['status']
                attendee['status'] = status
                if status != old_status:
                    if status == 'decline':
                        calendar.declineEvent(self)
                    if old_status == 'decline':
                        calendar.unDeclineEvent(self)
                self._p_changed = 1
                
        # Set up the dict for email notification
        mtool = getToolByName(calendar, 'portal_membership')
        userid = mtool.getAuthenticatedMember().getUserName()
        try:
            cn = self.getAttendeeInfo(calendar.getRpath()).get('cn', id)
        except AttributeError:
            cn = userid
        event_dict = {
            'id': userid,
            'request': 'status',
            'change': ({
                'attendee': calendar_rpath,
                'cn': cn,
                'type': self.getCalendar().usertype,
                'status': status,
                'comment': comment,
                'dtstamp': dtstamp,
                'sender': member,
                'sender_cn': member_cn,
             },)
        }
        
        # Change the status for all attendees calendars.
        # Get the attendeelist from the organizers calendar, 
        # since new attendees may have been added or old removed.
        org_calendar = self.getOrganizerCalendar()
        org_event = org_calendar._getOb(event_id)
        if org_event is None:
            LOG('NGCal', INFO, "Can't find original event for %s/%s" 
                % (calendar_rpath, event_id))
            return
        
        ctool = getToolByName(self, 'portal_cpscalendar')
        org_attendees = org_event.attendees
        
        for attendee in org_attendees:
            apath = attendee['rpath']
            # Skip this calendar
            if apath == calendar_rpath:
                continue
            acal = ctool.getCalendarForPath(apath, unrestricted=1)
            event = acal._getOb(event_id, None)
            if event is not None:
                event.setAttendeeStatus(calendar_rpath, status)
            
            # Check pending events
            for event in acal._pending_events:
                if event['id'] != event_id:
                    continue
                for att in event['event']['attendees']:
                    if att['rpath'] == calendar_rpath:
                        att['status'] = status
                        acal._p_changed = 1
                    
            # This needs some testing to see that it really does
            # the correct thing.
            acal.notifyMembers(event_dict)
                
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declareProtected('Add portal content', 'updateAttendeesCalendars')
    def updateAttendeesCalendars(self, comment='', attendees=None, 
                                 REQUEST=None, event_dict=None):
        """ 
        """
        notified_attendees = []
        all_attendees = []
        if event_dict is None:
            event_dict = self.getEventDict(comment=comment)
        caltool = getToolByName(self, 'portal_cpscalendar')
        this_rpath = self.getRpath()
        for attendee in self.attendees:
            attendee_rpath = attendee['rpath']
            all_attendees.append(attendee_rpath)
            if attendees is not None and attendee_rpath not in attendees:
                continue

            # Notify the relevant attendees except us.
            if attendee_rpath != this_rpath:
                # XXX: what's the visibility rule for invitations ?
                attendee_calendar = caltool.getCalendarForPath(
                    attendee_rpath, unrestricted=1)
                if attendee_calendar is None:
                    LOG('CPSCalendar', INFO, "Can't get calendar for %s" 
                        % (attendee_rpath, ))
                    continue
                attendee_calendar.addPendingEvent(event_dict)

            notified_attendees.append(attendee_rpath)

        calendar = self.getCalendar()
        calendar.notifyMembers(event_dict)
        self.notified_attendees = [rpath for rpath in all_attendees 
            if rpath in self.notified_attendees or rpath in notified_attendees]
        if all_attendees == self.notified_attendees:
            self.isdirty = 0
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declarePrivate('getEventInSlots')
    def getEventInSlots(self, start_time, end_time, slots):
        """
        """
        if self.event_type == 'event_recurring':
            return self._recurringMatch(start_time, end_time, slots)
        else:
            return self._standardMatch(start_time, end_time, slots,
                self.from_date, self.to_date)

    def getRecurrence(self, repeats):
        rstart = self.from_date
        from_year = self.from_date.year()
        from_month = self.from_date.month()
        from_day = self.from_date.day()
        to_hour = self.to_date.hour()
        to_minute = self.to_date.minute()
        rstop = DateTime(from_year, from_month, from_day, to_hour, to_minute)
        if self.recurrence_period == 'period_weekly':
            period = 'period_daily'
            repeats = repeats * 7
        elif self.recurrence_period == 'period_quarterly':
            period = 'period_monthly'
            repeats = repeats * 3
        else:
            period = self.recurrence_period

        if period == 'period_daily':
            return rstart + repeats, rstop + repeats
        if period == 'period_monthly':
            year, month, day, hour, minute, second, tz = rstart.parts()
            month = month + repeats
            while month > 12:
                month -= 12
                year += 1
            fromdate = DateTime(year, month, day, hour, minute, second, tz)
            year, month, day, hour, minute, second, tz = rstop.parts()
            month = month + repeats
            while month > 12:
                month -= 12
                year += 1
            todate = DateTime(year, month, day, hour, minute, second, tz)
            return fromdate, todate
        if period == 'period_yearly':
            year, month, day, hour, minute, second, tz = rstart.parts()
            year = year + repeats
            fromdate = DateTime(year, month, day, hour, minute, second, tz)
            year, month, day, hour, minute, second, tz = rstop.parts()
            year = year + repeats
            todate = DateTime(year, month, day, hour, minute, second, tz)
            return fromdate, todate
        raise ValueError('Unknown recurrence period %s for object %s' % (
            str(period), self.absolute_url()))

    def _recurringMatch(self, start_time, end_time, slots):
        if start_time.greaterThan(self.to_date):
            return []
        
        rstart, rstop = self.getRecurrence(0)
        repeats = 1
        while start_time.greaterThan(rstop):
            rstart, rstop = self.getRecurrence(repeats)
            repeats += 1

        if rstop.greaterThan(self.to_date):
            return []
        
        result = self._standardMatch(start_time, end_time, slots, rstart, rstop)
        while end_time.greaterThanEqualTo(rstart):
            rstart, rstop = self.getRecurrence(repeats)
            if rstop.greaterThan(self.to_date):
                break
            repeats += 1
            result.extend(self._standardMatch(start_time, end_time, slots,
                    rstart, rstop))
        return result

    def _standardMatch(self, start_time, end_time, slots, from_date, to_date):
        # Why redefine two built-in methods? /regebro
        def max(a, b):
            if a.lessThan(b):
                return b
            else:
                return a
        def min(a,b):
            if a.greaterThan(b):
                return b
            else:
                return a

        if (start_time.greaterThanEqualTo(to_date)
                or end_time.lessThanEqualTo(from_date)):
            return []
        result = []
        i = 0
        for start, stop in slots:
            if not (start.greaterThanEqualTo(to_date) or
                    stop.lessThanEqualTo(from_date)):
                result.append({
                  'event_id': self.id,
                  'event': self,
                  'start': max(start, from_date),
                  'stop': min(stop, to_date),
                  'slot': i,
                })
            i += 1
        return result

    def matchesTime(self, start, stop):
        event_start, event_stop = self.from_date, self.to_date
        repeats = 0
        if self.event_type == 'event_recurring':
            while start.greaterThan(event_stop):
                event_start, event_stop = self.getRecurrence(repeats)
                repeats += 1

        if event_stop > start and event_start < stop:
            return 1
        return 0

    def _getRequestInformations(self):
        """Return a tuple with current member name, his properties and
           a Datetime object
        """
        mtool = getToolByName(self, 'portal_membership')
        member = mtool.getAuthenticatedMember().getUserName()
        dtool = getToolByName(self, 'portal_directories')
        mdir = dtool.members
        entry = mdir.getEntry(member)
        if entry is not None:
            member_cn = entry.get(mdir.title_field, member)
        else:
            member_cn = member
        dtstamp = DateTime()
        return (member, member_cn, dtstamp)

    def manage_afterAdd(self, item, container):
        """Check if the event is canceled, then register it as
        canceled event."""
        CPSBaseDocument.manage_afterAdd(self, item, container)
        if aq_base(item) is aq_base(self):
            if self.event_status == 'canceled':
                calendar = self.getCalendar()
                calendar.cancelEvent(self)

InitializeClass(Event)

def addEvent(dispatcher, id, organizer=None, attendees=(), REQUEST=None, **kw):
    """Add an Event."""
    calendar = dispatcher.Destination()
    ctool = getToolByName(calendar, 'portal_cpscalendar')
    if organizer is None:
        # By default, organizer is the current calendar user
        try:
            organizer = ctool.getAttendeeInfo(calendar.getRpath())
        except AttributeError:
            mtool = getToolByName(calendar, 'portal_membership')
            dtool = getToolByName(calendar, 'portal_directories')
            uid = mtool.getAuthenticatedMember().getId()
            display_prop = mtool.members.title_field
            entry = dtool.members.getEntry(uid)
            if entry and entry.has_key(display_prop):
                ucn = entry[display_prop]
            else:
                ucn = uid
            organizer = {
                'id': mtool.getAuthenticatedMember().getId(),
                'rpath': calendar.getRpath(),
                'usertype': calendar.usertype,
                'cn': mtool.getAuthenticatedMember().getUserName(),
            }
    else:
        pass # Reached when responding to an invitation
    ob = Event(id, organizer=organizer, attendees=attendees, **kw)
    calendar._setObject(id, ob)

    if REQUEST is not None:
        url = dispatcher.DestinationURL()
        REQUEST.RESPONSE.redirect('%s/manage_main' % (url, ))


class VirtualEvent(Event):

    security = ClassSecurityInfo()
    display_type = 'freetime_event'

    def __init__(self, from_date=None, to_date=None):
        self.from_date = from_date
        self.to_date = to_date
        self.attendees = ()

    security.declarePublic('getCalendarUser')
    def getCalendarUser(self):
        return ''

    def absolute_url(self):
        return ''

InitializeClass(VirtualEvent)
