# Copyright (c) 2002-2003 Nuxeo SARL <http://nuxeo.com>
# Copyright (c) 2002 CIRB, Belgique
# Author: Julien Jalon <mailto:jj@nuxeo.com>
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

import string
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
     'title': 'Event',
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
                  'condition': '',
                  'permissions': (ModifyPortalContent,)},
                 {'id': 'attendees',
                  'name': 'action_attendees',
                  'action': 'string:${object_url}/calendar_attendees_form',
                  'permissions': (ModifyPortalContent,)},
                 {'id': 'delete',
                  'name': 'action_delete',
                  'action': 'string:${object_url}/calendar_delevent',
                  'condition': '',
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

    _properties = CPSBaseDocument._properties + (
        # FIXME: organizer is now a dictionary, so it doesn't make
        # sense to make it editable in a text field.
        {'id': 'organizer', 'type': 'text', 'mode': 'w', 'label': 'Organizer'},
        {'id': 'all_day', 'type': 'boolean', 'mode': 'w', 
         'label': 'All Day Event'},
        {'id': 'transparent', 'type': 'boolean', 'mode': 'w', 
         'label': 'Transparent Event'},
        {'id': 'location', 'type': 'text', 'mode': 'w', 'label': 'Location'},
        {'id': 'event_status', 'type': 'text', 'mode': 'w', 
         'label': 'Event Status'},
        {'id': 'category', 'type': 'text', 'mode': 'w', 'label': 'Category'},
    )

    #
    # Content accessors
    #

    organizer = {}
    attendees = ()
    from_date = None
    to_date = None
    all_day = 0
    location = ''
    event_status = 'unconfirmed'
    category = ''
    transparent = 0

    isdirty = 1
    notified_attendees = ()

    def __init__(self, id, organizer={}, attendees=(), 
                 from_date=None, to_date=None, **kw):
        LOG('CPSCalendar', DEBUG, "__init__ kw = ", kw)
        CPSBaseDocument.__init__(self, id, organizer=organizer, **kw)
        self.organizer = deepcopy(organizer)
        if attendees is not None:
            self.setAttendees(attendees)
        self.from_date = from_date 
        self.to_date = to_date
        self.all_day = kw.get('all_day')
        self.location = kw.get('location')
        self.event_status = kw.get('event_status')
        self.category = kw.get('category')
        self.transparent = kw.get('transparent')
        self._normalize()

    security.declareProtected('Modify portal content', 'edit')
    def edit(self, attendees=None, from_date=None, to_date=None, 
             all_day=None, transparent=None, **kw):
        """Edit method"""
        setdirty = 0
        old_status = self.event_status
        CPSBaseDocument.edit(self, **kw)
        new_status = self.event_status
        if new_status != old_status:
            if new_status == 'cancelled':
                calendar = self.getCalendar()
                calendar.addCancelledEvent(self)
            if old_status == 'cancelled':
                calendar = self.getCalendar()
                calendar.removeCancelledEvent(self)
            setdirty = 1

        if all_day is not None and (not self.all_day) != (not all_day):
            setdirty = 1
            self.all_day = all_day

        if transparent is not None:
            self.transparent = transparent

        if attendees is not None:
            self.setAttendees(attendees)
        if from_date is not None and self.from_date != from_date:
            setdirty = 1
            self.from_date = from_date
        if to_date is not None and self.to_date != to_date:
            setdirty = 1
            self.to_date = to_date
        self._normalize()

        if setdirty:
            self.isdirty = 1
            self.notified_attendees = ()

    def _normalize(self):
        """Normalize from_date and to_date attributes"""
        if self.all_day:
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

            if self.all_day:
                self._normalize()

    security.declareProtected(View, 'SearchableText')
    def SearchableText(self):
        """Used by the catalog for basic full text indexing."""
        return '%s %s' % (self.title, self.description)

    security.declareProtected(View, 'getCalendar')
    def getCalendar(self):
        """Return the calendar where this event is in"""
        return aq_parent(aq_inner(self))

    security.declareProtected(View, 'getCalendarUser')
    def getCalendarUser(self):
        """Return the id of the calendar instead of the user"""
        # XXX: we assume that calendar are directly stored on the
        # user's workspace
        return aq_parent(self.getCalendar())._owner[1]

    security.declareProtected(View, 'getOrganizerCalendar')
    def getOrganizerCalendar(self):
        """Return the calendar of the organizer of the event"""
        ctool = getToolByName(self, 'portal_cpscalendar')
        org_calendar = ctool.getCalendarForPath(self.organizer['rpath'])
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
                'all_day': self.all_day,
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
        """Return True if we are in the organizer's calendar"""
        return self.getCalendarUser() == self.organizer['id']

    security.declareProtected('Add portal content', 'isDirty')
    def isDirty(self):
        """Check if we can edit the event"""
        return not not ((self.isdirty and self.attendees and \
            self.canEditThisEvent()) or self.getPendingEvents())

    security.declareProtected('Add portal content', 'setEventStatus')
    def setEventStatus(self, status):
        """ 
        """
        old_status = self.event_status
        if status != old_status:
            if status == 'cancelled':
                calendar = self.getCalendar()
                calendar.addCancelledEvent(self)
            if old_status == 'cancelled':
                calendar = self.getCalendar()
                calendar.removeCancelledEvent(self)
            self.notified_attendees = ()
            self.isdirty = 1
        self.event_status = status

    security.declareProtected('Add portal content', 'setAttendees')
    def setAttendees(self, attendees):
        """Set atendees of the event from a attendees dictionary"""
        self.attendees = deepcopy(attendees)
        all_ids = tuple([at['id'] for at in attendees])
        self.notified_attendees = tuple(
            [id for id in self.notified_attendees if id in all_ids])
        self.isdirty = self.notified_attendees != all_ids

    security.declareProtected('Add portal content', 'setAttendeeStatus')
    def setAttendeeStatus(self, attendee, status):
        """Set the attendee's status"""
        change = 0
        for att in self.attendees:
            if att['id'] == attendee:
                att['status'] = status
                change = 1
        if change:
            self._p_changed = 1

    security.declareProtected('View', 'getMyStatus')
    def getMyStatus(self):
        """Return the status of the current calendar for this event"""
        my_id = self.getCalendarUser()
        for attendee in self.attendees:
            if attendee['id'] == my_id:
                return attendee['status']

    security.declareProtected('Add portal content', 'setMyStatus')
    def setMyStatus(self, status, comment='', REQUEST=None):
        """Set the status for the current calendar"""
        user_id = self.getCalendarUser()
        (member, member_cn, dtstamp) = self._getRequestInformations()
        for attendee in self.attendees:
            if attendee['id'] == user_id:
                old_status = attendee['status']
                attendee['status'] = status
                if status != old_status:
                    if status == 'decline':
                        calendar = self.getCalendar()
                        calendar.addDeclinedEvent(self)
                    if old_status == 'decline':
                        calendar = self.getCalendar()
                        calendar.removeDeclinedEvent(self)
                self._p_changed = 1
        org_calendar = self.getOrganizerCalendar()
        if org_calendar is None:
            LOG('NGCal', INFO, "Can't get calendar for %s" 
                % (self.organizer['id'], ))
            return
        my_id = self.getCalendarUser()

        try:
            cn = self.getAttendeeInfo(my_id).get('cn', id)
        except AttributeError:
            mtool = getToolByName(calendar, 'portal_membership')
            cn = mtool.getAuthenticatedMember().getUserName()

        org_calendar.addPendingEvent({
            'id': self.id,
            'request': 'status',
            'change': ({
                'attendee': my_id,
                'cn': cn,
                'type': self.getCalendar().usertype,
                'status': status,
                'comment': comment,
                'dtstamp': dtstamp,
                'sender': member,
                'sender_cn': member_cn,
            },)
        })
        
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declareProtected('Add portal content', 'updateAttendeesCalendars')
    def updateAttendeesCalendars(self, comment='', attendees=None, 
                                 REQUEST=None):
        """ 
        """
        notified_attendees = []
        all_attendees = []
        event_dict = self.getEventDict(comment=comment)
        calendar = self.getCalendar()
        calendars = aq_parent(aq_inner(calendar))
        for attendee in self.attendees:
            attendee_rpath = attendee['rpath']
            all_attendees.append(attendee_rpath)
            if attendees is not None and attendee_rpath not in attendees:
                continue
            attendee_calendar = calendars.getCalendarForPath(attendee_rpath)
            if attendee_calendar is None:
                LOG('CPSCalendar', INFO, "Can't get calendar for %s" 
                    % (attendee_id, ))
                continue
            attendee_calendar.addPendingEvent(event_dict=event_dict)
            notified_attendees.append(attendee_id)

        self.notified_attendees = [id for id in all_attendees 
            if id in self.notified_attendees or id in notified_attendees]
        if all_attendees == self.notified_attendees:
            self.isdirty = 0
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declarePrivate('getEventInSlots')
    def getEventInSlots(self, start_time, end_time, slots):
        """
        """
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

        if (start_time.greaterThanEqualTo(self.to_date) 
                or end_time.lessThanEqualTo(self.from_date)):
            return None
        result = []
        for start, stop in slots:
            if (start.greaterThanEqualTo(self.to_date) or
                    stop.lessThanEqualTo(self.from_date)):
                result.append(None)
            else:
                result.append({
                  'event_id': self.id,
                  'event': self,
                  'start': max(start, self.from_date),
                  'stop': min(stop, self.to_date),
                })
        return result

        
    def _getRequestInformations(self):
        """Return a tuple with current member name, his properties and 
           a Datetime object
        """
        mtool = getToolByName(self, 'portal_membership')
        member = mtool.getAuthenticatedMember().getUserName()
        dirtool = getToolByName(self, 'portal_metadirectories')
        members = dirtool.members
        entry = members.getEntry(member)
        if entry is not None:
            member_cn = entry.get(members.display_prop, member)
        else:
            member_cn = member
        dtstamp = DateTime()
        return (member, member_cn, dtstamp)

    def manage_afterAdd(self, item, container):
        """Check if the event is cancelled, then register it as
        cancelled event."""
        CPSBaseDocument.manage_afterAdd(self, item, container)
        if aq_base(item) is aq_base(self):
            if self.event_status == 'cancelled':
                calendar = self.getCalendar()
                calendar.addCancelledEvent(self)

InitializeClass(Event)

def addEvent(dispatcher, id, organizer=None, attendees=(), REQUEST=None, **kw):
    """Add an Event."""
    calendar = dispatcher.Destination()
    if organizer is None:
        # By default, organizer is the current calendar user
        try:
            organizer = calendar.getAttendeeInfo(calendar.rpath)
        except AttributeError:
            mtool = getToolByName(calendar, 'portal_membership')
            organizer = {
                'id': mtool.getAuthenticatedMember().getId(),
                'usertype': calendar.usertype,
                'cn': mtool.getAuthenticatedMember().getUserName(),
            }
    else:
        raise "XXX: Is this line ever reached ???"
    ob = Event(id, organizer=organizer, attendees=attendees, **kw)
    calendar._setObject(id, ob)
    ob = getattr(calendar, id)
    if REQUEST is not None:
        url = dispatcher.DestinationURL()
        REQUEST.RESPONSE.redirect('%s/manage_main' % (url, ))
