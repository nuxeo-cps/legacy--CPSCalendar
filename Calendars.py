# (c) 2002 Nuxeo SARL <http://nuxeo.com>
# (c) 2002 Florent Guillaume <mailto:fg@nuxeo.com>
# (c) 2002 Préfecture du Bas-Rhin, France
# See license info at the end of this file.
# $Id$

"""
  Calendars container
"""

from zLOG import LOG, DEBUG

from Acquisition import aq_parent, aq_inner, aq_base
from DateTime import DateTime

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

from Products.CMFCore.CMFCorePermissions import \
     setDefaultRoles, View, ManageProperties
from Products.CMFCore.utils import getToolByName

from Products.CPSCore.CPSBase import CPSBaseFolder, CPSBase_adder
#from Products.NuxWorkgroup.Workgroup import Workgroup, ManageWorkgroups

ManageWorkgroups = 'Manage Workgroups'
setDefaultRoles(ManageWorkgroups, ('Manager',))


WorkgroupManager = 'WorkgroupManager'
WorkgroupMember = 'WorkgroupMember'
WorkgroupVisitor = 'WorkgroupVisitor'
WorkgroupManagerRoles = (WorkgroupManager, WorkgroupMember, WorkgroupVisitor,)
WorkgroupMemberRoles = (WorkgroupMember, WorkgroupVisitor,)
WorkgroupVisitorRoles = (WorkgroupVisitor,)

factory_type_information = (
    {'id': 'Calendars',
     'title': 'Calendars',
     'icon': 'calendars_icon.gif',
     'product': 'CPSCalendar',
     'meta_type': 'Calendars',
     'factory': 'addCalendars',
     'immediate_view': 'folder_edit_form',
     'filter_content_types': 1,
     'allowed_content_types': (
                               'Calendar',
                               ),
     'actions': ({'id': 'view',
                  'name': '_action_view_',
                  'action': 'calendars_contents',
                  'permissions': (View,),
                  'category': 'object',
                  },
                 {'id': 'localroles',
                  'name': '_action_access_rights_',
                  'action': 'folder_localrole_form',
                  'permissions': (ManageWorkgroups,),
                  'category': 'object'
                  },
                 {'id': 'create',
                  'name': '_action_create_',
                  'action': 'calendars_create_form',
                  'visible': 0,
                  'permissions': ()},
                 {'id': 'isproxytype',
                  'name': 'isproxytype',
                  'action': 'folder',
                  'permissions': ('',),
                  'visible': 0},
                 ),
     },
    )

def cmp_ev(a, b):
    return cmp(b['start'], a['start'])

def slot_union(cal_slot, with_free=0):
    result = []
    if not cal_slot:
        return []
    cal_slot = cal_slot[:]
    cal_slot.sort(cmp_ev)
    ev = cal_slot.pop()
    start = ev['start']
    stop = ev['stop']
    if with_free:
        y, mo, d, h, m, x, x = start.parts()
        start_height = h*60 + m
        if start_height:
            result.append({
                'busy': 0,
                'height': start_height,
                'start': DateTime(y, mo, d),
            })
    while cal_slot:
        ev = cal_slot.pop()
        if stop.lessThan(ev['start']):
            if with_free:
                x, x, x, h, m, x, x = stop.parts()
                stop_height = h*60 + m
                if not stop_height:
                    stop_height = 1440
                result.append({
                  'busy': 1,
                  'height': stop_height - start_height
                })
            else:
                result.append({
                  'start': start,
                  'stop': stop,
                })
            start = ev['start']
            if with_free:
                x, x, x, h, m, x, x = start.parts()
                start_height = h*60 + m
                free_time = start_height - stop_height
                if free_time:
                    result.append({
                      'busy': 0,
                      'height': free_time,
                      'start': stop,
                    })
            stop = ev['stop']
        else:
            stop = max(ev['stop'], stop)
    if with_free:
        x, x, x, h, m, x, x = stop.parts()
        stop_height = h*60 + m
        if not stop_height:
            stop_height = 1440
        result.append({
          'busy': 1,
          'height': stop_height - start_height,
        })
        if stop_height < 1439:
            free_time = 1440 - stop_height
            result.append({
              'busy': 0,
              'height': free_time,
              'start': stop,
            })
    else:
        result.append({
          'start': start,
          'stop': stop,
        })

    return result

class Calendars(CPSBaseFolder):
    """
    """
    meta_type = 'Calendars'

    portal_type = meta_type

    security = ClassSecurityInfo()

    _properties = ({'id':'title', 'type':'string'},
                   {'id':'description', 'type':'text'},
                   )

    isDocumentContainer = 0

    # XXX use a special permission here
    security.declareProtected('View', 'unionCals')
    def unionCals(self, *cals, **kw):
        if not cals:
            return []
        if kw.get('with_free'):
            with_free = 1
        result = []
        length = len(cals[0])
        for i in range(length):
            this_slot = []
            for cal in cals:
                this_slot.extend(cal[i])
            result.append(slot_union(this_slot, with_free=with_free))
        return result

    security.declareProtected('View', 'getFreeBusy')
    def getFreeBusy(self, attendees, from_date, to_date,
                    from_time_hour, from_time_minute,
                    to_time_hour, to_time_minute):
        """Gets free/busy informations on attendees calendars"""
        # normalize
        start_time = DateTime(from_date.year(), from_date.month(), from_date.day())
        to_date = to_date + 1
        end_time = DateTime(to_date.year(), to_date.month(), to_date.day())
        slot_start = start_time
        slots = []
        while slot_start.lessThan(end_time):
            slots.append((slot_start, slot_start+1))
            slot_start += 1
            slot_start = DateTime(slot_start.year(), slot_start.month(), slot_start.day())

        length = len(slots)

        # first create the mask calendar
        mask_cal = []
        if (to_time_hour or to_time_minute) and \
            (from_time_hour > to_time_hour or \
                (from_time_hour == to_time_hour and \
                    from_time_minute > to_time_minute)):
            from_time_hour, to_time_hour = to_time_hour, from_time_hour
            from_time_minute, to_time_minute = to_time_minute, from_time_minute

        for slot in slots:
            this_day = []
            date = slot[0]
            year = date.year()
            month = date.month()
            day = date.day()
            if from_time_hour or from_time_minute:
                mask_from = DateTime(year, month, day, from_time_hour, from_time_minute)
                this_day.append({
                    'start': date,
                    'stop': mask_from,
                })

            if to_time_hour or to_time_minute:
                mask_to = DateTime(year, month, day, to_time_hour, to_time_minute)
                this_day.append({
                    'start': mask_to,
                    'stop': slot[1],
                })
            mask_cal.append(this_day)

        ids = self.objectIds('Calendar')
        ids = [id for id in attendees if id in ids]
        cals_dict = {}
        cal_users = {}
        for id in ids:
            calendar = self.getCalendarForId(id)
            cal_users[id] = self.getAttendeeInfo(id)['cn']
            calendar_slots = []
            for i in range(len(slots)):
                calendar_slots.append([])
            slots_done = [None] * length
            for event in calendar.objectValues('Event'):
                if event.transparent:
                    continue
                event_slots = event.getEventInSlots(
                    start_time, end_time, slots
                )
                if event_slots is None:
                    continue
                i = 0
                for event_slot in event_slots:
                    if event_slot is not None and slots_done[i] is None:
                        if event.all_day:
                            slots_done[i] = {
                                'start': event_slot['start'],
                                'stop': event_slot['stop'],
                            }
                        else:
                            calendar_slots[i].append({
                                'start': event_slot['start'], 
                                'stop': event_slot['stop']
                            })
                    i += 1
            cals_dict[id] = list = []
            i = 0
            for cal_slot in calendar_slots:
                if slots_done[i] is not None:
                    list.append([slots_done[i]])
                else:
                    list.append(slot_union(cal_slot))
                i += 1
            
        return {
            'cal_users': cal_users,
            'cals_dict': cals_dict,
            'mask_cal': mask_cal,
            'slots': slots,
        }

    security.declareProtected(View, 'getCalendarForId')
    def getCalendarForId(self, id):
        """Gets calendar for id, creates it if id is a user"""
        id = str(id)
        ids = self.objectIds('Calendar')
        if id in ids:
            return getattr(self, id)
        context = aq_parent(aq_inner(self))
        dirtool = getToolByName(context, 'portal_metadirectories')
        members = dirtool.members
        entry_prop = members._getInternalEntryProp()
        entry = members._getEntry(id) 
        if entry:
            # create this calendar for this member
            ttool = getToolByName(context, 'portal_types')
            ti = ttool.getTypeInfo('Calendar')
            # do ti.constructInstance(self, id) without permission checks
            p = self.manage_addProduct[ti.product]
            m = getattr(p, ti.factory)
            kw = {}
            if getattr(m, 'isDocTemp', 0):
                args = (m.aq_parent, self.REQUEST)
                kw['id'] = id
            else:
                args = (id, )

            kw['title'] = 'Calendar of %s' % (id, )
            
            m(*args, **kw)
            ob = self._getOb(id)
            ob._computedtitle = 1
            ti._finishConstruction(ob)

            mtool = getToolByName(context, 'portal_membership')
            if not mtool.isAnonymousUser():
                current_user = mtool.getAuthenticatedMember().getUserName()
                ob.manage_delLocalRoles(userids=[current_user])
            ob.manage_setLocalRoles(id, ['WorkgroupManager', 'WorkgroupMember', 'WorkgroupVisitor'])
            ob.reindexObject()
            return ob
        return None

    security.declareProtected(View, 'getCalendarsDict')
    def getCalendarsDict(self, exclude=None):
        calendars_dict = {}
        for ob in self.objectValues('Calendar'):
            entry = calendars_dict.setdefault(ob.usertype, [])
            if exclude is None or exclude != ob.id:
                entry.append({
                  'id': ob.id,
                  'cn': ob.title_or_id(),
                  'usertype': ob.usertype,
                })
        return calendars_dict

    security.declarePublic(View, 'getAttendeeInfo')
    def getAttendeeInfo(self, id, status=0):
        if id in self.objectIds('Calendar'):
            calendar = getattr(self, id)
            info = {
                'id': id,
                'usertype': calendar.usertype,
            }
            if calendar.usertype != 'member':
                info['cn'] = calendar.title_or_id()
            else:
                dirtool = getToolByName(self, 'portal_metadirectories')
                members = dirtool.members
                entry = members.getEntry(id)
                if entry is None:
                    info['cn'] = id
                else:
                    info['cn'] = entry.get(members.display_prop, id)
        else:
            # maybe a member with no created calendar
            dirtool = getToolByName(self, 'portal_metadirectories')
            members = dirtool.members
            entry = members.getEntry(id)
            if entry is None:
                return None
            else:
                info = {
                    'id': id,
                    'usertype': 'member',
                    'cn': entry.get(members.display_prop, id),
                }
        if status:
            info['status'] = 'unconfirmed'
        return info

    security.declareProtected('View', 'getVisibleCalendars')
    def getVisibleCalendars(self):
        mtool = getToolByName(self, 'portal_membership')
        cals = []
        for cal in self.objectValues('Calendar'):
            if mtool.checkPermission('View', cal):
                cals.append(cal)
        return cals

    security.declareProtected('Access contents information', 'get')
    def get(self, name, default=None):
        """
        """
        try:
            return self[name]
        except KeyError:
            return default

    def __getitem__(self, name):
        ob = self.getCalendarForId(name)
        if ob is not None:
            return ob
        raise KeyError, name

InitializeClass(Calendars)

def addCalendars(dispatcher, id,
                 title='',
                 description='',
                 REQUEST=None):
    """Adds a Calendars container."""
    ob = Calendars(id)#, title, description)
    container = dispatcher.Destination()
    #container._setObject(id, ob)
    #ob = container._getOb(id)
    if REQUEST is not None:
        url = dispatcher.DestinationURL()
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)
    return CPSBase_adder(container, ob, REQUEST=REQUEST)


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
