# (c) 2002 Nuxeo SARL <http://nuxeo.com>
# (c) 2002 Florent Guillaume <mailto:fg@nuxeo.com>
# (c) 2002 Préfecture du Bas-Rhin, France
# See license info at the end of this file.
# $Id$

"""
  Events container
"""

from zLOG import LOG, DEBUG, INFO
from copy import deepcopy
from DateTime import DateTime
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Acquisition import aq_inner, aq_parent

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import \
     View, ManageProperties

from Products.NuxWorkgroup.Workgroup import Workgroup, ManageWorkgroups

def cmp_ev(a, b):
    return a['start'].__cmp__(b['start'])

factory_type_information = (
    {'id': 'Calendar',
     'title': 'Calendar',
     'icon': 'calendar_icon.gif',
     'product': 'NuxGroupCalendar',
     'meta_type': 'Calendar',
     'factory': 'addCalendar',
     'immediate_view': 'calendar_view',
     'filter_content_types': 1,
     'allowed_content_types': (
                               'Event',
                               ),
     'actions': ({'id': 'view',
                  'name': '_action_view_',
                  'action': 'calendar_view',
                  'permissions': (View,),
                  'category': 'object',
                  'visible': 0,
                  },
                 {'id': 'month_view',
                  'name': '_action_month_view_',
                  'action': 'calendar_view?disp=month',
                  'permissions': (View,),
                  'category': 'object'
                  },
                 {'id': 'week_view',
                  'name': '_action_week_view_',
                  'action': 'calendar_view?disp=week',
                  'permissions': (View,),
                  'category': 'object'
                  },
                 {'id': 'day_view',
                  'name': '_action_day_view_',
                  'action': 'calendar_view?disp=day',
                  'permissions': (View,),
                  'category': 'object'
                  },
                 {'id': 'addevent',
                  'name': '_action_addevent_',
                  'action': 'calendar_addevent_form?all_day=1',
                  'permissions': ("Add portal content",),
                  'category': 'object'
                  },
                 {'id': 'export',
                  'name': '_action_export_',
                  'action': 'calendar_export',
                  'permissions': (View,),
                  'category': 'object'
                  },
                 {'id': 'localroles',
                  'name': '_action_access_rights_',
                  'action': 'workgroup_localrole_form',
                  'permissions': (ManageWorkgroups,),
                  'category': 'object'
                  },
                 {'id': 'create',
                  'name': '_action_create_',
                  'action': 'calendar_create_form',
                  'visible': 0,
                  'permissions': ()},
                 ),
     },
    )


class Calendar(Workgroup):
    """
    """
    meta_type = 'Calendar'

    security = ClassSecurityInfo()

    _properties = ({'id':'title', 'type':'string'},
                   {'id':'description', 'type':'text'},
                   {'id':'usertype', 'type':'string'},
                   )

    isDocumentContainer = 0
    isCalendar = 1

    usertype = 'member'

    # Workgroup dynamic title
    _basetitle = '_cal_Calendar_of_%s_'

    _pending_events = ()
    _declined = ()
    _canceled = ()

    def __init__(self, id, title='', description='', usertype='member'):
        Workgroup.__init__(self, id, title, description)
        self.usertype = usertype

    security.declareProtected('Add portal content', 'getPendingEventsCount')
    def getPendingEventsCount(self):
        """Get count of pending events
        """
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
        """Add an event request
        """
        if event_dict['request'] == 'status' and \
                event_dict['id'] not in self.objectIds():
            # status change lost because this event was once deleted
            return
        base_dict = event_dict
        event_dict = deepcopy(event_dict)
        events = []
        this_event = None
        for event in self._pending_events:
            if event['id'] == event_dict['id']:
                this_event = event
            else:
                events.append(event)

        if event_dict['request'] == 'status':
            # append status change
            if this_event is not None:
                event_dict['change'] = this_event['change'] + event_dict['change']
        events.append(event_dict)
        self._pending_events = tuple(events)
        self._notifyMembers(base_dict)

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
        events = [event for event in self._pending_events if event['id'] != event_id]
        self._pending_events = tuple(events)
        if REQUEST is not None:
            if request == 'status':
                REQUEST.RESPONSE.redirect("%s/%s/calendar_attendees_form" % (self.absolute_url(), event_id))
            else:
                REQUEST.RESPONSE.redirect("%s/%s" % (self.absolute_url(), event_id))

    security.declareProtected('Add portal content', 'cleanPendingEvents')
    def cleanPendingEvents(self, id=None, REQUEST=None):
        """
        """
        if id is None:
            self._pending_events = ()
        else:
            self._pending_events = tuple([ev for ev in self._pending_events if ev['id'] != id])
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declareProtected('View', 'getEventsDesc')
    def getEventsDesc(self, start_time, end_time, disp):
        """Returns events between start_time and end_time
        formatted according for a disp display type.

        disp can be 'day', 'month', 'view'
        """
        if disp == 'day':
            slots = [(start_time, end_time)]
            slot_list = [{'desc': start_time, 'day': [], 'hour': []}]
        elif disp == 'week':
            slot_start = start_time
            slots = []
            slot_list = []
            for i in range(0,7):
                slots.append((slot_start, slot_start+1))
                slot_list.append({
                  'desc': slot_start,
                  'day': [],
                  'hour': [],
                })
                slot_start += 1
        elif disp == 'month':
            slot_start = start_time
            slots = []
            slot_list = []
            while slot_start.lessThan(end_time):
                slots.append((slot_start, slot_start+1))
                slot_list.append({
                  'desc': slot_start,
                  'day': [],
                  'hour': [],
                })
                slot_start += 1
                slot_start = DateTime(slot_start.year(), slot_start.month(), slot_start.day())
        events = self.objectValues()
        for event in events:
            event_slots = event.getEventInSlots(start_time, end_time, slots)
            if event_slots is not None:
                key = event.all_day and 'day' or 'hour'
                i = 0
                for slot_desc in slot_list:
                    event_slot = event_slots[i]
                    if event_slot is not None:
                        slot_desc[key].append(event_slot)
                    i += 1

        # reform result for correct display according to disp
        if disp == 'day':
            hour_cols = [slot_list[0]['hour']]
            return {
              'slots': slots,
              'day_events': slot_list[0]['day'],
              'hour_blocks': self._get_hour_block_cols(hour_cols)[0],
            }
        elif disp == 'week':
            day_events_list = [slot['day'] for slot in slot_list]
            hour_cols = [slot['hour'] for slot in slot_list]
            day_lines = self._get_day_lines(day_events_list, len(slots))
            hour_block_cols = self._get_hour_block_cols(hour_cols)
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
            current_line = [None]*(current_day-1)
            current_dict = {
              'hour_cols': current_line,
            }
            lines.append(current_dict)
            day_events_list = [[]]*(current_day-1)
            i = 0
            for slot in slot_list:
                slot_day = slot['day']
                day_events_list.append(slot_day)
                slot_hour = slot['hour']
                slot_hour.sort(cmp_ev)
                slot = slots[i]
                i += 1
                current_line.append({
                    'hour': slot_hour,
                    'slot': slot,
                    'dom': i,
                    'day_height': len(slot_hour),
                })
                if current_day == 7:
                    day_lines = self._get_day_lines(day_events_list, 7)
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
                day_events_list.extend([[]]*(8-current_day))
                day_lines = self._get_day_lines(day_events_list, 7)
                current_dict['day_lines'] = day_lines
                current_line.extend([None]*(8-current_day))
            return {
                'slots': slots,
                'lines': lines,
            }

    def _get_day_lines(self, day_events_list, len_slots):
        day_lines = []
        day_ids = []
        day_dict = {}
        day_occupation = []
        day_empty = []
        hour_cols = []
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
                        day_lines[line].append(
                            {
                                'event': None,
                                'colspan': empty_span,
                                'pos': pos,
                            }
                        )
                    day_lines[line].append(
                        {
                            'event': ev['event'],
                        }
                    )
            i += 1
        i = 0
        for day_line in day_lines:
            id = day_occupation[i]
            if id is None:
                pos = day_empty[i]
                empty_span = len_slots - pos
                if empty_span > 0:
                    day_line.append(
                        {
                            'event': None,
                            'colspan': empty_span,
                            'pos': pos,
                        }
                    )
            else:
                line, colstart = day_dict[id]
                day_lines[line][-1]['colspan'] = len_slots - colstart
            i += 1

        return day_lines

    def _get_hour_block_cols(self, hour_cols):
        hour_block_cols = []
        for col in hour_cols:
            blocks = []
            hour_block_cols.append(blocks)
            if not col:
                continue
            col.sort(cmp_ev)
            conflict = []
            conflict_start = 0
            conflict_stop = 0
            last_ev = 0
            for ev in col:
                start = ev['start']
                stop = ev['stop']
                start_min = start.hour()*60+start.minute()
                stop_min = stop.hour()*60+stop.minute()
                if stop_min == 0:
                    stop_min = 1440
                if conflict:
                    # event conflict
                    if conflict_stop <= start_min:
                        # this event does not have conflicts
                        # so resolve conflict
                        if len(conflict) == 1:
                            # just a simple event
                            blocks.append([[{
                              'event': conflict[0]['ev']['event'],
                              'height': conflict[0]['stop_min'] - conflict[0]['start_min'],
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
                                correct_col.append({
                                    'event': c_ev['event'],
                                    'height': conf_stop - conf_start
                                })
                                block_stops[i] = conf_stop
                            blocks.append(block_cols)
                                
                        conflict = []
                        last_ev = conflict_stop
                    else:
                        # this event provoques conflicts
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
                            'event':None,
                            'height':start_min - last_ev,
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
                    blocks.append([[{
                      'event': conflict[0]['ev']['event'],
                      'height': conflict[0]['stop_min'] - conflict[0]['start_min'],
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
                        correct_col.append({
                            'event': ev['event'],
                            'height': conf_stop - conf_start
                        })
                        block_stops[i] = conf_stop
                    blocks.append(block_cols)
                last_ev = conflict_stop

            if last_ev < 1439:
                blocks.append([[{
                    'event': None,
                        'height': 1439 - last_ev
                    }]])

        return hour_block_cols

    def _get_email_for(self, member, dir):
        """
        """
        member_prop = dir.getEntry(member)
        if member_prop is None:
            return None
        return member_prop.get('email')

    def _notifyMembers(self, event_dict):
        """Notify members when a pending event arrives
        """
        
        # get mailhost object
        mailhost = getattr(self, 'MailHost')
        if mailhost is None:
            LOG('NGCal', INFO, "Can't get MailHost object")
            return

        # get current user email
        mtool = self.portal_membership
        dir = self.portal_metadirectories.members
        member = mtool.getAuthenticatedMember().getUserName()
        mail_from = self._get_email_for(member, dir)
        if mail_from is None:
            LOG('NGCal', INFO, "Can't get email address for %s" % (mail_from, ))
            return

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
            if 'WorkgroupMember' in roles:
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
                email = self._get_email_for(id, dir)
                if email is not None:
                    mails[email] = None
                done[id] = None

        mails = mails.keys()

        # usefull vars
        calendar_title = self.title_or_id()
        calendar_url = self.absolute_url()
        event = getattr(self, event_dict['id'], None)
        if event is None:
            event_title = event_dict['event']['title']
        else:
            event_title = event.title_or_id()

        mailing = self.calendar_mailing_notify(event_dict, calendar_url, calendar_title, event_title, mail_from, mails)
        LOG('NGCal', DEBUG, 'Notifying from %s to %s:\n%s' % (mail_from, mails, mailing, ))
        try:
            mailhost.send(mailing,
                mto=mails,
                mfrom=mail_from,
                subject="[CAL] %s" % (event_title, ),
                encode='8bit')
        except:
            LOG('NGCal', INFO, "Error while sending notification email")

    security.declareProtected('View', 'getEvents')
    def getEvents(from_date, to_date):
        return ()

    security.declarePrivate('addDeclinedEvent')
    def addDeclinedEvent(self, event):
        event_id = event.id
        if event_id not in self._declined:
            self._declined = self._declined + (event_id, )

    security.declarePrivate('addCanceledEvent')
    def addCanceledEvent(self, event):
        event_id = event.id
        if event_id not in self._canceled:
            self._canceled = self._canceled + (event_id, )

    security.declarePrivate('removeDeclinedEvent')
    def removeDeclinedEvent(self, event):
        event_id = event.id
        if event_id in self._declined:
            self._declined = tuple([id for id in self._declined if id != event_id])

    security.declarePrivate('removeCanceledEvent')
    def removeCanceledEvent(self, event):
        event_id = event.id
        if event_id in self._canceled:
            self._canceled = tuple([id for id in self._canceled if id != event_id])

    security.declareProtected('Add portal content', 'getDeclinedCanceledEvents')
    def getDeclinedCanceledEvents(self):
        """
        """
        return {
            'canceled': self._canceled,
            'declined': self._declined,
        }

    security.declareProtected('Delete objects', 'manage_delObjects')
    def manage_delObjects(self, ids, *args, **kw):
        """
        """
        self._pending_events = tuple([ev for ev in self._pending_events if ev['id'] not in ids])
        declined = [id for id in self._declined if id not in ids]
        canceled = [id for id in self._canceled if id not in ids]
        Workgroup.manage_delObjects(self, ids, *args, **kw)
        self._declined = tuple(declined)
        self._canceled = tuple(canceled)

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
        roles=['Manager', 'WorkgroupManager', 'WorkgroupMember', 'WorkgroupVisitor'],
        acquire=0)
    ob.manage_permission(
        permission_to_manage='View',
        roles=['Manager', 'WorkgroupManager', 'WorkgroupMember', 'WorkgroupVisitor'],
        acquire=0)
    ob.manage_permission(
        permission_to_manage='Add portal content',
        roles=['Manager', 'WorkgroupManager', 'WorkgroupMember'],
        acquire=0)
    ob.manage_permission(
        permission_to_manage='Modify portal content',
        roles=['Manager', 'WorkgroupManager', 'WorkgroupMember'],
        acquire=0)

    if REQUEST is not None:
        url = dispatcher.DestinationURL()
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)


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
