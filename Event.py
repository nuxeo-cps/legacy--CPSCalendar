# (c) 2002 Nuxeo SARL <http://nuxeo.com>
# (c) 2002 Julien Jalon <mailto:jj@nuxeo.com>
# (c) 2002 CIRB, Belgique
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

from Products.NuxCPSDocuments.BaseDocument import BaseDocument, BaseDocument_adder


factory_type_information = (
    {'id': 'Event',
     'title': 'Event',
     'content_icon': 'event_icon.gif',
     'product': 'NuxGroupCalendar',
     'factory': 'addEvent',
     'meta_type': 'Event',
     'immediate_view': 'event_edit_form',
     'allow_discussion': 0,
     'filter_content_types': 0,
     'actions': ({'id': 'view',
                  'name': '_action_view_',
                  'action': 'calendar_event_view',
                  'permissions': (View,)},
                 {'id': 'edit',
                  'name': '_action_modify_',
                  'action': 'calendar_editevent_form',
                  'permissions': (ModifyPortalContent,)},
                 {'id': 'attendees',
                  'name': '_action_attendees_',
                  'action': 'calendar_attendees_form',
                  'permissions': (ModifyPortalContent,)},
                 {'id': 'delete',
                  'name': '_action_delete_',
                  'action': 'calendar_delevent',
                  'permissions': (ModifyPortalContent,)},
                 {'id': 'create',
                  'name': '_action_create_',
                  'action': 'calendar_eventcreate_form',
                  'visible': 0,
                  'permissions': ()},
                )
     },
    )


class Event(BaseDocument):
    """
    Event
    """
    meta_type = 'Event'

    security = ClassSecurityInfo()

    _properties = BaseDocument._properties + (
        {'id':'organizer', 'type':'text', 'mode':'w', 'label':'Organizer'},
        {'id':'all_day', 'type':'boolean', 'mode':'w', 'label':'All Day Event'},
        {'id':'transparent', 'type':'boolean', 'mode':'w', 'label':'Transparent Event'},
        {'id':'location', 'type':'text', 'mode':'w', 'label':'Location'},
        {'id':'event_status', 'type':'text', 'mode':'w', 'label':'Event Status'},
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
    transparent = 0

    isdirty = 1

    def __init__(self, id, organizer={}, attendees=(), from_date=None, to_date=None, **kw):
        BaseDocument.__init__(self, id, organizer=organizer, **kw)
        self.organizer = deepcopy(organizer)
        self.attendees = deepcopy(attendees)
        self.from_date = from_date
        self.to_date = to_date
        self._normalize()

    security.declareProtected('Modify portal content', 'edit')
    def edit(self, attendees=None, from_date=None, to_date=None, all_day=None, transparent=None, **kw):
        old_status = self.event_status
        BaseDocument.edit(self, **kw)
        new_status = self.event_status
        if new_status != old_status:
            if new_status == 'canceled':
                calendar = self.getCalendar()
                calendar.addCanceledEvent(self)
            if old_status == 'canceled':
                calendar = self.getCalendar()
                calendar.removeCanceledEvent(self)

        if all_day is not None:
            self.all_day = all_day

        if transparent is not None:
            self.transparent = transparent

        if attendees is not None:
            self.attendees = deepcopy(attendees)
        if from_date is not None:
            self.from_date = from_date
        if to_date is not None:
            self.to_date = to_date
        self._normalize()

        self.isdirty = 1

    def _normalize(self):
        if self.all_day:
            from_date = self.from_date
            if from_date is not None:
                time_since_daystart = from_date.hour()*3600+from_date.minute()*60+from_date.second()
                if time_since_daystart:
                    timeTime = from_date.timeTime()
                    self.from_date = DateTime(timeTime - time_since_daystart)
            to_date = self.to_date
            if to_date is not None:
                time_since_daystart = to_date.hour()*3600+to_date.minute()*60+to_date.second()
                if time_since_daystart != 86399:
                    timeTime = to_date.timeTime()
                    self.to_date = DateTime(timeTime - time_since_daystart + 86399)
        if self.to_date.lessThan(self.from_date):
            to_date = self.to_date
            self.to_date = self.from_date
            self.from_date = to_date

            if self.all_day:
                self._normalize()

    security.declareProtected(View, 'SearchableText')
    def SearchableText(self):
        """
        Used by the catalog for basic full text indexing.
        """
        return '%s %s %s' % (self.title,
                                self.description,)

    security.declareProtected(View, 'getCalendar')
    def getCalendar(self):
        """
        """
        return aq_parent(aq_inner(self))

    security.declareProtected(View, 'getCalendarUser')
    def getCalendarUser(self):
        """
        """
        return self.getCalendar().id

    security.declareProtected(View, 'getOrganizerCalendar')
    def getOrganizerCalendar(self):
        """
        """
        calendar = self.getCalendar()
        calendars = aq_parent(aq_inner(calendar))
        org_calendar = calendars.get(self.organizer['id'])
        return org_calendar

    security.declareProtected(View, 'getAttendeesDict')
    def getAttendeesDict(self):
        """
        """
        attendees_dict = {}
        for attendee in self.attendees:
            entry = attendees_dict.setdefault(attendee['usertype'], [])
            entry.append(deepcopy(attendee))
        return attendees_dict

    security.declareProtected('Add portal content', 'getPendingEvents')
    def getPendingEvents(self):
        """
        """
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
                'all_day': self.all_day,
                'title': self.title,
                'description': self.description,
                'location': self.location,
                'event_status': self.event_status,
                'comment': comment,
                'dtstamp': dtstamp,
                'sender': member,
                'sender_cn': member_cn,
            }
        }

    security.declareProtected('View', 'canEditThisEvent')
    def canEditThisEvent(self):
        """
        """
        return self.getCalendarUser() == self.organizer['id']

    security.declareProtected('Add portal content', 'setEventStatus')
    def setEventStatus(self, status):
        """
        """
        old_status = self.event_status
        if status != old_status:
            if status == 'canceled':
                calendar = self.getCalendar()
                calendar.addCanceledEvent(self)
            if old_status == 'canceled':
                calendar = self.getCalendar()
                calendar.removeCanceledEvent(self)
            self.isdirty = 1
        self.event_status = status

    security.declareProtected('Add portal content', 'setAttendees')
    def setAttendees(self, attendees):
        """
        """
        self.attendees = deepcopy(attendees)
        self.isdirty = 1

    security.declareProtected('Add portal content', 'setAttendeeStatus')
    def setAttendeeStatus(self, attendee, status):
        """
        """
        change = 0
        for att in self.attendees:
            if att['id'] == attendee:
                att['status'] = status
                change = 1
        if change:
            self.isdirty = 1
            self._p_changed = 1

    security.declareProtected('View', 'getMyStatus')
    def getMyStatus(self):
        my_id = self.getCalendarUser()
        for attendee in self.attendees:
            if attendee['id'] == my_id:
                return attendee['status']

    security.declareProtected('Add portal content', 'setMyStatus')
    def setMyStatus(self, status, comment='', REQUEST=None):
        """
        """
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
            LOG('NGCal', INFO, "Can't get calendar for %s" % (self.organizer['id'], ))
            return
        my_id = self.getCalendarUser()
        org_calendar.addPendingEvent({
            'id': self.id,
            'request': 'status',
            'change': ({
                'attendee': my_id,
                'cn': self.getAttendeeInfo(my_id).get('cn', id),
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
    def updateAttendeesCalendars(self, comment='', REQUEST=None):
        """
        """
        if not self.isdirty:
            LOG('NGCal', INFO, 'Event %s does not need to be updated' % self.id)
            return
        event_dict = self.getEventDict(comment=comment)
        calendar = self.getCalendar()
        calendars = aq_parent(aq_inner(calendar))
        for attendee in self.attendees:
            attendee_id = attendee['id']
            attendee_calendar = calendars.getCalendarForId(attendee_id)
            if attendee_calendar is None:
                LOG('NGCal', INFO, "Can't get calendar for %s" % (attendee_id, ))
                continue
            attendee_calendar.addPendingEvent(event_dict=event_dict)
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

        if start_time.greaterThanEqualTo(self.to_date) or end_time.lessThanEqualTo(self.from_date):
            return None
        result = []
        for start, stop in slots:
            if start.greaterThanEqualTo(self.to_date) or \
                stop.lessThanEqualTo(self.from_date):
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
        """
        """
        BaseDocument.manage_afterAdd(self, item, container)
        if aq_base(item) is aq_base(self):
            if self.event_status == 'canceled':
                calendar = self.getCalendar()
                calendar.addCanceledEvent(self)

InitializeClass(Event)

def addEvent(dispatcher, id, organizer=None, attendees=(), REQUEST=None, **kw):
    """Add an Event."""
    calendar = dispatcher.Destination()
    if organizer is None:
        # by default, organizer is the current calendar user

        organizer = calendar.getAttendeeInfo(calendar.id)
    ob = Event(id, organizer=organizer, attendees=attendees, **kw)
    calendar._setObject(id, ob)
    ob = getattr(calendar, id)
    if REQUEST is not None:
        url = dispatcher.DestinationURL()
        REQUEST.RESPONSe.redirect('%s/manage_main' % (url, ))
