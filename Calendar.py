# -*- coding: iso-8859-15 -*-
# Copyright (c) 2002-2003 Nuxeo SARL <http://nuxeo.com>
# Copyright (c) 2002 Préfecture du Bas-Rhin, France
# Author: Florent Guillaume <mailto:fg@nuxeo.com>

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

# $Id$

"""
  A Calendar is an Events container
"""

from zLOG import LOG, DEBUG, INFO
from copy import deepcopy
import time, random
from DateTime import DateTime
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Acquisition import aq_inner, aq_parent

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import setDefaultRoles, View
from Products.CMFCore.CMFCorePermissions import ChangePermissions

from Products.CPSCore.CPSBase import CPSBaseFolder#, CPSBase_adder
#from Products.NuxWorkgroup.Workgroup import Workgroup, ManageWorkgroups

from Event import Event

ManageWorkgroups = 'Manage Workspaces'
setDefaultRoles(ManageWorkgroups, ('Manager',))


WorkgroupManager = 'WorkspaceManager'
WorkgroupMember = 'WorkspaceMember'
WorkgroupVisitor = 'WorkspaceReader'
WorkgroupManagerRoles = (WorkgroupManager, WorkgroupMember, WorkgroupVisitor,)
WorkgroupMemberRoles = (WorkgroupMember, WorkgroupVisitor,)
WorkgroupVisitorRoles = (WorkgroupVisitor,)

ACCESS_CONTENTS_INFO_ROLES = ['Manager', 'WorkspaceManager', 'WorkspaceMember',
                              'WorkspaceReader']
VIEW_ROLES = ['Manager', 'WorkspaceManager', 'WorkspaceMember',
               'WorkspaceReader']
ADD_PORTAL_CONTENT_ROLES = ['Manager', 'WorkspaceManager', 'WorkspaceMember']
MODIFY_PORTAL_CONTENT_ROLES = ['Manager', 'WorkspaceManager', 'WorkspaceMember']

def cmpEv(a, b):
    return a['start'].__cmp__(b['start'])

factory_type_information = (
    {'id': 'Calendar',
     'title': 'portal_type_Calendar_title',
     'description': 'portal_type_Calendar_description',
     'icon': 'calendar_icon.gif',
     'product': 'CPSCalendar',
     'meta_type': 'Calendar',
     'factory': 'addCalendar',
     'immediate_view': 'calendar_view',
     'filter_content_types': 1,
     'allowed_content_types': ('Event',),
     'actions': ({'id': 'view',
                  'name': 'action_view',
                  'action': 'string:${object_url}/calendar_view',
                  'condition': '',
                  'permissions': (View,),
                  'category': 'object',
                  'visible': 0,
                  },
                 {'id': 'month_view',
                  'name': 'action_month_view',
                  'action': 'string:${object_url}/calendar_view?disp=month',
                  'condition': '',
                  'permissions': (View,),
                  'category': 'object',
                  },
                 {'id': 'week_view',
                  'name': 'action_week_view',
                  'action': 'string:${object_url}/calendar_view?disp=week',
                  'condition': '',
                  'permissions': (View,),
                  'category': 'object',
                  },
                 {'id': 'day_view',
                  'name': 'action_day_view',
                  'action': 'string:${object_url}/calendar_view?disp=day',
                  'condition': '',
                  'permissions': (View,),
                  'category': 'object',
                  },
                 {'id': 'calendar_event_viewer',
                  'name': 'action_calendar_event_viewer',
                  'action': 'string:${object_url}/calendar_event_viewer?disp=week',
                  'condition': "",
                  'permissions': (View,),
                  'category': 'object',
                  },
                 {'id': 'addevent',
                  'name': 'action_addevent',
                  'action': 'string:${object_url}/calendar_addevent_form',
                  'condition': '',
                  'permissions': ("Add portal content",),
                  'category': 'object',
                  },
                 {'id': 'meeting',
                  'name': 'action_addmeeting',
                  'action': 'string:${object_url}/calendar_meeting_form',
                  'permissions': ("Add portal content",),
                  'category': 'object',
                  },
                 {'id': 'display',
                  'name': 'action_display',
                  'action': 'string:${object_url}/calendar_display_form',
                  'condition': '',
                  'permissions': ("Add portal content",),
                  'category': 'object',
                  },
                 {'id': 'edit',
                  'name': 'action_modify',
                  'action': 'string:${object_url}/calendar_edit_form',
                  'condition': '',
                  'permissions': (View,),
                  'category': 'object',
                  },
                 {'id': 'export',
                  'name': 'action_export',
                  'action': 'string:${object_url}/calendar_export',
                  'condition': '',
                  'permissions': (View,),
                  'category': 'object',
                  },
                 {'id': 'action_local_roles',
                  'name': 'action_local_roles',
                  'action': 'string:${object_url}/folder_localrole_form',
                  'condition': '',
                  'permissions': (ChangePermissions,),
                  'category': 'object',
                  },
                 {'id': 'create',
                  'name': 'action_create',
                  'action': 'string:${object_url}/calendar_create_form',
                  'condition': '',
                  'permissions': (),
                  'visible': 0,},
                 ),
     },
    )


class Calendar(CPSBaseFolder):
    """A calendar contains events"""

    meta_type = 'Calendar'
    security = ClassSecurityInfo()

    _properties = ({'id': 'title', 'type': 'string'},
                   {'id': 'description', 'type': 'text'},
                   {'id': 'usertype', 'type': 'string'},
                   )

    isDocumentContainer = 0

    _pending_events = ()
    _declined = ()
    _canceled = ()

    _additional_cals = ()

    # XXX: make this editable properties.
    # XXX: these are "view" properties. This should go to a "view" class.
    first_hour = 8
    last_hour = 20
    # XXX: there are still many places where this value is hardcoded in the
    # skins
    cell_height = 20

    event_types = [ 'event_tofrom',     # To a time from a time
                    'event_allday',     # From a date to a date
                    'event_recurring']  # Repeats
    period_types = ['period_daily',
                    'period_weekly',
                    'period_monthly',
                    'period_quarterly', # Every three months
                    'period_yearly',
                    ]

    def __init__(self, id, title='', description='', usertype='member'):
        # XXX: title and description not used. Why ?
        kw = {}
        kw['title'] = title
        kw['description'] = description
        self.uid = self.genUid()
        CPSBaseFolder.__init__(self, id, **kw)
        self.usertype = usertype

    #
    # We don't use this yet
    #
    security.declarePrivate('genUid')
    def genUid(self):
        """UID generator. To be improved (so that uids are truly unique) and
        moved to a base class later."""
        return str(int(time.time())) + str(random.randint(0, 1000))

    def createEvent(self, *args, **kw):
        uid = self.genUid()
        event = Event(id=uid, **kw)
        self._setObject(uid, event)
        return uid


    security.declarePrivate('getOwnerId')
    def getOwnerId(self):
        # getOwner() is part of the Zope API
        return self.getOwner(1)[1]
    
    security.declarePublic('getCalendarUser')
    def getCalendarUser(self):
        """Return the id of the calendar instead of the user"""
        # XXX: we assume that calendar are directly stored on the
        # user's workspace
        # In almost all cases this will return the same as getOwnerId, 
        # so it's a bit of rendundancy, but some scripts use this one,
        return aq_parent(self).getOwner(1)[1]

    security.declarePublic('getRpath')
    def getRpath(self):
        return self.absolute_url()[len(self.portal_url())+1:]

    security.declareProtected('Add portal content', 'getPendingEventsCount')
    def getPendingEventsCount(self):
        """Get count of pending events"""
        return len(self._pending_events)

    security.declareProtected('Add portal content', 'getPendingEvents')
    def getPendingEvents(self, event_id=None):
        if event_id is None:
            return self._pending_events
        events = []
        for event in self._pending_events:
            if event['id'] == event_id:
                events.append(event)
        return tuple(events)

    security.declarePublic('addPendingEvent')
    def addPendingEvent(self, event_dict):
        """Add an event request"""
        # print event_dict
        if event_dict['request'] == 'status' and \
                event_dict['id'] not in self.objectIds('Event'):
            # Status change lost because this event was once deleted
            return
        base_dict = event_dict
        event_dict = deepcopy(event_dict)
        events = []
        this_event = event_dict
        for event in self._pending_events:
            if event['id'] == event_dict['id']:
                this_event = event
            else:
                events.append(event)

        if event_dict['request'] == 'status':
            # Append status change
            if this_event is not None:
                event_dict['change'] = this_event['change'] \
                    + event_dict['change']
        events.append(event_dict)
        self._pending_events = tuple(events)

    security.declareProtected('Add portal content', 'confirmPendingEvent')
    def confirmPendingEvent(self, event_id, REQUEST=None, **kw):
        """
        """
        if REQUEST is not None:
            kw.update(REQUEST.form)
        pending = None
        for event in self._pending_events:
            if event['id'] == event_id:
                pending = event
                break
        if event is None:
            return
        request = pending['request']
        if request == 'request':
            status = kw.get('status')
            event = getattr(self, event_id, None)
            if event is None:
                self.invokeFactory('Event', **pending['event'])
                event = getattr(self, event_id)
            else:
                kw = pending['event']
                event.edit(**kw)
            if status is not None:
                event.setMyStatus(status)
        elif request == 'status':
            event = getattr(self, event_id, None)
            if event is None:
                return
            for change in pending['change']:
                event.setAttendeeStatus(change['attendee'], change['status'])
        events = [event for event in self._pending_events
                        if event['id'] != event_id]
        self._pending_events = tuple(events)
        if REQUEST is not None:
            if request == 'status':
                REQUEST.RESPONSE.redirect("%s/%s/calendar_attendees_form"
                    % (self.absolute_url(), event_id))
            else:
                REQUEST.RESPONSE.redirect("%s/%s"
                    % (self.absolute_url(), event_id))

    security.declareProtected('Add portal content', 'cleanPendingEvents')
    def cleanPendingEvents(self, event_id=None, REQUEST=None):
        """
        """
        if event_id is None:
            self._pending_events = ()
        else:
            self._pending_events = tuple(
                [ev for ev in self._pending_events if ev['id'] != event_id])
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declareProtected('View', 'getEventsDesc')
    def getEventsDesc(self, start_time, end_time, disp, additional=1):
        """Return events between start_time and end_time formatted according
        for a disp display type.

        disp can be 'day', 'month', 'week'
        """
        assert disp in ('day', 'month', 'week')

        mtool = getToolByName(self, 'portal_membership')
        show = mtool.checkPermission('List folder contents', self)

        slots = []
        slot_list = []
        if disp == 'day':
            slots = [(start_time, end_time)]
            slot_list = [{'desc': start_time, 'day': [], 'hour': []}]
        elif disp == 'week':
            slot_start = start_time
            for i in range(0, 7):
                slots.append((slot_start+i, slot_start+i+1))
                slot_list.append({
                  'desc': slot_start,
                  'day': [],
                  'hour': [],
                })
        elif disp == 'month':
            slot_start = start_time
            while slot_start.lessThan(end_time):
                slots.append((slot_start, slot_start+1))
                slot_list.append({
                  'desc': slot_start,
                  'day': [],
                  'hour': [],
                })
                slot_start += 1
                slot_start = DateTime(slot_start.year(), slot_start.month(),
                                      slot_start.day())

        events = self.objectValues('Event')
        if additional and self._additional_cals:
            mtool = getToolByName(self, 'portal_membership')
            caltool = getToolByName(self, 'portal_cpscalendar')
            cal_rpaths = [rpath for rpath in caltool.listCalendarPaths()
                          if rpath in self._additional_cals]
            for cal_rpath in cal_rpaths:
                cal = caltool.getCalendarFromPath(cal_rpath)
                if self.getRpath() != cal_rpath and \
                   mtool.checkPermission('List folder contents', cal):
                    events.extend(cal.objectValues('Event'))

        for event in events:
            event_slots = event.getEventInSlots(start_time, end_time, slots)
            if event_slots:
                key = event.event_type == 'event_allday' and 'day' or 'hour'
                for event_slot in event_slots:
                    if event_slot is not None:
                        slot = event_slot['slot']
                        slot_desc = slot_list[slot]
                        slot_desc[key].append(event_slot)

        # reform result for correct display according to disp
        if disp == 'day':
            hour_cols = [slot_list[0]['hour']]
            return {
              'slots': slots,
              'day_events': slot_list[0]['day'],
              'hour_blocks':
                  self._getHourBlockCols(hour_cols, show)[0],
            }
        elif disp == 'week':
            day_events_list = [slot['day'] for slot in slot_list]
            hour_cols = [slot['hour'] for slot in slot_list]
            day_lines = self._getDayLines(day_events_list, len(slots))
            hour_block_cols = self._getHourBlockCols(hour_cols, show)
            return {
                'slots': slots,
                'day_lines': day_lines,
                'hour_block_cols': hour_block_cols,
            }
        elif disp == 'month':
            lines = []
            current_day = start_time.dow()
            if current_day == 0:
                current_day = 7
            current_line = [None] * (current_day - 1)
            current_dict = {
              'hour_cols': current_line,
            }
            lines.append(current_dict)
            day_events_list = [[]] * (current_day - 1)
            i = 0
            for slot in slot_list:
                slot_day = slot['day']
                day_events_list.append(slot_day)
                slot_hour = slot['hour']
                slot_hour.sort(cmpEv)
                slot = slots[i]
                i += 1
                current_line.append({
                    'hour': slot_hour,
                    'slot': slot,
                    'dom': i,
                    'day_height': len(slot_hour),
                })
                if current_day == 7:
                    day_lines = self._getDayLines(day_events_list, 7)
                    current_dict['day_lines'] = day_lines
                    day_events_list = []
                    current_day = 1
                    current_line = []
                    current_dict = {
                        'hour_cols': current_line,
                    }
                    lines.append(current_dict)
                else:
                    current_day += 1
            if current_day > 1:
                day_events_list.extend([[]] * (8 - current_day))
                day_lines = self._getDayLines(day_events_list, 7)
                current_dict['day_lines'] = day_lines
                current_line.extend([None] * (8 - current_day))
            return {
                'slots': slots,
                'lines': lines,
            }

    def _getDayLines(self, day_events_list, len_slots):
        """
        """
        day_lines = []
        day_ids = []
        day_dict = {}
        day_occupation = []
        day_empty = []
        i = 0
        for day_events in day_events_list:
            event_ids = [ev['event_id'] for ev in day_events]
            remove_ids = [id for id in day_ids if id not in event_ids]
            for id in remove_ids:
                line, colstart = day_dict[id]
                day_lines[line][-1]['colspan'] = i - colstart
                day_occupation[line] = None
                del day_dict[id]
                day_ids.remove(id)
                day_empty[line] = i
            for ev in day_events:
                id = ev['event_id']
                if id not in day_ids:
                    try:
                        line = day_occupation.index(None)
                    except ValueError:
                        line = len(day_occupation)
                        day_lines.append([])
                        day_occupation.append(None)
                        day_empty.append(0)
                    day_occupation[line] = id
                    day_ids.append(id)
                    day_dict[id] = (line, i)
                    pos = day_empty[line]
                    empty_span = i - pos
                    if empty_span:
                        day_lines[line].append({
                            'event': None,
                            'colspan': empty_span,
                            'pos': pos,
                        })
                    day_lines[line].append({
                        'event': ev['event'],
                    })
            i += 1
        i = 0
        for day_line in day_lines:
            id = day_occupation[i]
            if id is None:
                pos = day_empty[i]
                empty_span = len_slots - pos
                if empty_span > 0:
                    day_line.append({
                        'event': None,
                        'colspan': empty_span,
                        'pos': pos,
                    })
            else:
                line, colstart = day_dict[id]
                day_lines[line][-1]['colspan'] = len_slots - colstart
            i += 1

        return day_lines

    def _getHourBlockCols(self, hour_cols, show):
        """
        """
        MIN_HEIGHT = 50 # The minimum display height of an event.
        hour_block_cols = []
        for col in hour_cols:
            blocks = []
            hour_block_cols.append(blocks)
            if not col:
                continue
            col.sort(cmpEv)
            conflict = []
            conflict_start = 0
            conflict_stop = 0
            last_ev = self.first_hour * 60
            for ev in col:
                start = ev['start']
                # If event starts before our visualisation window, we
                # make it start at the start of our visualisation window.
                if start.hour() < self.first_hour:
                    start_min = self.first_hour * 60
                else:
                    start_min = start.hour() * 60 + start.minute()
                stop = ev['stop']
                # Same for end of event.
                if stop.hour() > self.last_hour:
                    stop_min = self.last_hour * 60
                else:
                    stop_min = stop.hour() * 60 + stop.minute()

                # We're off the window.
                if stop_min <= start_min:
                    continue

                if stop_min == 0:
                    stop_min = 1440
                if conflict:
                    # event conflict
                    if conflict_stop <= start_min:
                        # this event does not have conflicts
                        # so resolve conflict
                        if len(conflict) == 1:
                            # just a simple event
                            the_event = conflict[0]['ev']['event']
                            height = conflict[0]['stop_min'] - \
                                     conflict[0]['start_min']
                            if height < MIN_HEIGHT:
                                conflict[0]['stop_min'] += MIN_HEIGHT - height
                                height = MIN_HEIGHT
                            blocks.append([[{
                              'event': the_event,
                              'height': height,
                              'isdirty': show and the_event.isDirty()
                            }]])
                        else:
                            block_cols = []
                            block_stops = []
                            for conf in conflict:
                                c_ev = conf['ev']
                                conf_start = conf['start_min']
                                conf_stop = conf['stop_min']
                                i = -1
                                correct_i = -1
                                for correct_stop in block_stops:
                                    if correct_stop <= conf_start:
                                        correct_i = i
                                        break
                                    i += 1
                                i = correct_i
                                if i == -1:
                                    i = len(block_cols)
                                    block_cols.append([])
                                    block_stops.append(conflict_start)
                                    correct_stop = conflict_start

                                correct_col = block_cols[i]
                                if conf_start > correct_stop:
                                    correct_col.append({
                                        'event': None,
                                        'height': conf_start - correct_stop
                                    })
                                the_event = c_ev['event']
                                height = conf_stop - conf_start
                                if height < MIN_HEIGHT:
                                    conf_stop += MIN_HEIGHT - height
                                    height = MIN_HEIGHT
                                correct_col.append({
                                    'event': the_event,
                                    'height': height,
                                    'isdirty': \
                                        show and the_event.isDirty(),
                                })
                                block_stops[i] = conf_stop
                            blocks.append(block_cols)

                        conflict = []
                        last_ev = conflict_stop
                    else:
                        # This event provoques conflicts
                        # so add this event to conflict's resolve
                        conflict.append({
                          'start_min': start_min,
                          'stop_min': stop_min,
                          'ev': ev,
                        })
                        conflict_stop = max(stop_min, conflict_stop)
                if not conflict:
                    if last_ev != start_min:
                        blocks.append([[{
                            'event': None,
                            'height': start_min - last_ev,
                        }]])
                    conflict_start = start_min
                    conflict_stop = stop_min
                    conflict.append({
                      'start_min': start_min,
                      'stop_min': stop_min,
                      'ev': ev
                    })
            if conflict:
                if len(conflict) == 1:
                    the_event = conflict[0]['ev']['event']
                    height = conflict[0]['stop_min'] - conflict[0]['start_min']
                    if height < MIN_HEIGHT:
                        conflict[0]['stop_min'] += MIN_HEIGHT - height
                        height = MIN_HEIGHT
                    blocks.append([[{
                      'event': the_event,
                      'height': height,
                      'isdirty': show and the_event.isDirty(),
                    }]])
                else:
                    block_cols = []
                    block_stops = []
                    for conf in conflict:
                        ev = conf['ev']
                        conf_start = conf['start_min']
                        conf_stop = conf['stop_min']
                        i = -1
                        correct_i = -1
                        for correct_stop in block_stops:
                            if correct_stop <= conf_start:
                                correct_i = i+1
                                break
                            i += 1
                        i = correct_i
                        if i == -1:
                            i = len(block_cols)
                            block_cols.append([])
                            block_stops.append(conflict_start)
                            correct_stop = conflict_start

                        correct_col = block_cols[i]
                        if conf_start > correct_stop:
                            correct_col.append({
                                'event': None,
                                'height': conf_start - correct_stop
                            })
                        the_event = ev['event']
                        height = conf_stop - conf_start
                        if height < MIN_HEIGHT:
                            conf_stop += MIN_HEIGHT - height
                            height = MIN_HEIGHT
                        correct_col.append({
                            'event': the_event,
                            'height': height,
                            'isdirty': show and the_event.isDirty(),
                        })
                        block_stops[i] = conf_stop
                    blocks.append(block_cols)
                last_ev = conflict_stop

        return hour_block_cols

    security.declarePrivate('getEmail')
    def getEmail(self, member, directory):
        """Get email from member's properties in directory"""
        try:
            memberob = directory.getEntry(member)
            if not memberob:
                return None
            return memberob.get('email')
        except KeyError:
            # The user has an member data entry, but is not a member.
            return None

    security.declarePrivate('notifyMembers')
    def notifyMembers(self, event_dict):
        """Notify members when a pending event arrives"""
        if not event_dict.has_key('event'):
            return
        # Get mailhost object through acquisition
        mailhost = self.MailHost

        # Get current user email
        mtool = getToolByName(self, 'portal_membership')
        dtool = getToolByName(self, 'portal_directories')
        mdir = dtool.members
        member = mtool.getAuthenticatedMember().getUserName()
        mail_from = self.getEmail(member, mdir)
        if mail_from is None:
            LOG('NGCal', INFO, "Can't get email address for %s"
                % (mail_from, ))
            return
        reply_to = mail_from
        m = getattr(self, 'get_apparent_mail_from', None)
        if m is not None:
            mail_from = m()

        # XXX: all this is probably wrong
        # get local roles for members
        merged = {}
        object = aq_inner(self)
        while 1:
            if hasattr(object, '__ac_local_roles__'):
                dict = object.__ac_local_roles__ or {}
                if callable(dict): dict = dict()
                for k, v in dict.items():
                    if merged.has_key(k):
                        merged[k] = merged[k] + v
                    else:
                        merged[k] = v
            # groups
            if hasattr(object, '__acl_local_group_roles__'):
                dict = object.__ac_local_group_roles__ or {}
                if callable(dict): dict = dict()
                for k, v in dict.items():
                    k = 'group:'+k
                    if merged.has_key(k):
                        merged[k] = merged[k] + v
                    else:
                        merged[k] = v
            # end groups
            parent = aq_parent(object)
            if parent is not None:
                object = aq_inner(aq_parent(object))
                continue
            if hasattr(object, 'im_self'):
                object = aq_inner(object.im_self)
                continue
            break

        # get ids for members
        ids = {}
        for id, roles in merged.items():
            if 'WorkspaceMember' in roles:
                ids[id] = None

        # extend groups
        member_ids = []
        aclu = self.acl_users
        if hasattr(aclu, 'getGroupById'):
            for id in ids.keys():
                if id.startswith('group:'):
                    gid = id[len('group:'):]
                    group = aclu.getGroupById(gid, None)
                    if group is not None:
                        users = group.getUsers()
                        member_ids.extend(users)
                else:
                    member_ids.append(id)
        else:
            member_ids = ids.keys()

        done = {}
        mails = {}
        for id in member_ids:
            if not done.has_key(id):
                email = self.getEmail(id, mdir)
                if email is not None:
                    mails[id] = email
                done[id] = None

        for attendee in event_dict['event']['attendees']:
            id = attendee.get('id')
            if id is None:
                continue
            if attendee['status'] == 'unconfirmed':
                email = self.getEmail(id, mdir)
                if email:
                    mails[id] = email

        event = getattr(self, event_dict['id'], None)
        if event is None:
            new_event = 1
            event_title = event_dict['event']['title']
        else:
            new_event = 0
            event_title = event.title_or_id()

        caltool = getToolByName(self, 'portal_cpscalendar')
        calendar_title = self.title_or_id()
        
        for id, mail in mails.items():
            calendar = caltool.getCalendarForUser(id)
            if calendar is None:
                continue
            calendar_url = calendar.absolute_url()
            mailing = self.calendar_mailing_notify(event_dict, calendar_url,
                calendar_title, event_title, new_event=new_event)
            try:
                mailhost.send(mailing, mto=mail, mfrom=mail_from,
                        subject="[CAL] %s" % event_title, encode='8bit')
            except:
                import sys
                LOG('CPSCalendar', INFO, 
                    "Error while sending notification email",
                    error = sys.exc_info())

    security.declareProtected('View', 'getEvents')
    def getEvents(self, from_date, to_date, by_days = 0):
        """Return all events with from_date and to_date in the interval
            by_days option make it return events in a list of days
        """
        events = self.objectValues('Event')
        if by_days:
            days = int(to_date-from_date)
            events_list = []
            for i in range(0, days):
                day_list = []
                start = from_date + i
                end = from_date + i + 1
                for event in events:
                    if event.matchesTime(start, end):
                        day_list.append(event)
                events_list.append(day_list)
            return events_list
        else:
            return [event for event in events
                    if event.matchesTime(from_date, to_date)]

    security.declarePrivate('declineEvent')
    def declineEvent(self, event):
        """Add the event id in the self._declined list"""
        event_id = event.id
        if event_id not in self._declined:
            self._declined = self._declined + (event_id, )

    security.declarePrivate('cancelEvent')
    def cancelEvent(self, event):
        """Add the event id in the self._canceled list"""
        event_id = event.id
        if event_id not in self._canceled:
            self._canceled = self._canceled + (event_id, )

    security.declarePrivate('unDeclineEvent')
    def unDeclineEvent(self, event):
        """Remove event from declined events list"""
        event_id = event.id
        if event_id in self._declined:
            self._declined = tuple(
                [id for id in self._declined if id != event_id])

    security.declarePrivate('unCancelEvent')
    def unCancelEvent(self, event):
        """Remove event from canceled events lists"""
        event_id = event.id
        if event_id in self._canceled:
            self._canceled = tuple(
                [id for id in self._canceled if id != event_id])

    security.declareProtected('Add portal content', 'getDeclinedCanceledEvents')
    def getDeclinedCanceledEvents(self):
        """Return a dictionary with canceled events ids and declined
        events ids"""
        return {
            'canceled': self._canceled,
            'declined': self._declined,
        }

    security.declareProtected('Add portal content', 'setAdditionalCalendars')
    def setAdditionalCalendars(self, calendars):
        """
        """
        self._additional_cals = tuple(calendars)

    security.declareProtected('Add portal content', 'getAdditionalCalendars')
    def getAdditionalCalendars(self):
        """
        """
        return self._additional_cals

    security.declareProtected('Add portal content', 'getAdditionalCalendars')
    def getAdditionalCalendarObjs(self):
        """
        """
        ctool = getToolByName(self, 'portal_calendar')
        return filter(None,
            [ctool.getCalendarFromPath(x) for x in self._additional_cals])

    security.declareProtected('Delete objects', 'manage_delObjects')
    def manage_delObjects(self, ids, *args, **kw):
        """Override manage_delObjects to cleanup declined and canceled
        events lists."""
        self._pending_events = tuple(
            [ev for ev in self._pending_events if ev['id'] not in ids])
        declined = [id for id in self._declined if id not in ids]
        canceled = [id for id in self._canceled if id not in ids]
        CPSBaseFolder.manage_delObjects(self, ids, *args, **kw)
        self._declined = tuple(declined)
        self._canceled = tuple(canceled)

    def upgradePendingEvents(self, REQUEST=None):
        """Upgrades pending events"""
        pending_events = []
        upgradecount = 0
        for each in deepcopy(self._pending_events):
            if not each.has_key('event'):
                continue
            event = each['event']
            if event.has_key('event_type'):
                pending_events.append(each)
            else:
                upgradecount += 1
                if event.get('all_day', 0):
                    event['event_type'] = 'event_allday'
                else:
                    event['event_type'] = 'event_tofrom'
                pending_events.append(each)
                    
        if upgradecount:
            self._pending_events = pending_events
            # Return a string even if there is no request, for use in logging 
            # when running the install.
            return "Upgraded %s pending events for %s" % (str(upgradecount), 
                self.absolute_url())
        if REQUEST is not None:
            return "No upgrade needed"
        else:
            return 0
        

InitializeClass(Calendar)


def addCalendar(dispatcher, id,
                 title='',
                 description='',
                 usertype='member',
                 REQUEST=None, **kw):
    """Adds an Events container."""
    ob = Calendar(id, title, description, usertype)
    container = dispatcher.Destination()
    container._setObject(id, ob)
    ob = container._getOb(id)
    # sets correct permissions on ob
    ob.manage_permission(
        permission_to_manage='Access contents information',
        roles=ACCESS_CONTENTS_INFO_ROLES,
        acquire=0)
    ob.manage_permission(
        permission_to_manage='View',
        roles=VIEW_ROLES,
        acquire=0)
    ob.manage_permission(
        permission_to_manage='Add portal content',
        roles=ADD_PORTAL_CONTENT_ROLES,
        acquire=0)
    ob.manage_permission(
        permission_to_manage='Modify portal content',
        roles=MODIFY_PORTAL_CONTENT_ROLES,
        acquire=0)

    if REQUEST is not None:
        url = dispatcher.DestinationURL()
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)

