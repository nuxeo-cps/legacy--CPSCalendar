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
     View, ManageProperties
from Products.CMFCore.utils import getToolByName


from Products.NuxWorkgroup.Workgroup import Workgroup, ManageWorkgroups

factory_type_information = (
    {'id': 'Calendars',
     'title': 'Calendars',
     'icon': 'calendars_icon.gif',
     'product': 'NuxGroupCalendar',
     'meta_type': 'Calendars',
     'factory': 'addCalendars',
     'immediate_view': 'workgroup_edit_form',
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
                  'action': 'workgroup_localrole_form',
                  'permissions': (ManageWorkgroups,),
                  'category': 'object'
                  },
                 {'id': 'create',
                  'name': '_action_create_',
                  'action': 'calendars_create_form',
                  'visible': 0,
                  'permissions': ()},
                 ),
     },
    )

def slot_union(base, new_slot):
    start_new = new_slot['start']
    stop_new = new_slot['stop']
    start_pos = -1
    stop_pos = -1
    next_to = 0
    prev_to = -1
    i = 0
    for start, stop in base:
        if stop.lessThan(start_new):
            next_to = i+1
        elif stop.lessThanEqualTo(stop_new):
            start_pos = i
        elif start.lessThanEqualTo(stop_new):
            prev_to = i+1
            stop_pos = i
            break
        else:
            prev_to = i
            break
        i += 1
    part1 = base[:next_to]
    if prev_to == -1: prev_to = i
    print next_to, start_pos, stop_pos, prev_to
    part2 = base[prev_to:]
    center = (start_new, stop_new)
    if start_pos > -1:
        start_new = min(start_new, base[start_pos][0])
        center = (start_new, stop_new)
    if stop_pos > -1:
        base_slot = base[stop_pos]
        start_new = min(center[0], base_slot[0])
        center = (start_new, base_slot[1])
    return part1 + [center] + part2

class Calendars(Workgroup):
    """
    """
    meta_type = 'Calendars'

    portal_type = meta_type

    security = ClassSecurityInfo()

    _properties = ({'id':'title', 'type':'string'},
                   {'id':'description', 'type':'text'},
                   )

    isDocumentContainer = 0

    security.declareProtected('Get FreeBusy', 'getFreeBusy')
    def getFreeBusy(self, attendees, from_date, to_date):
        """Gets free/busy informations on attendees calendars"""
        # normalize
        start_time = DateTime(from_date.year(), from_date.month, from_date.day())
        end_time = DateTime(to_date.year(), to_date.month, to_date.day())
        slot_start = start_time
        slots = []
        while slot_start.lessThan(end_time):
            slots.append((slot_start, slot_start+1))
            slot_start += 1
            slot_start = DateTime(slot_start.year(), slot_start.month(), slot_start.day())

        ids = self.objectIds('Calendar')
        ids = [id for id in attendees if id not in ids]
        allcal_slots = [[]] * len(slots)
        for id in ids:
            calendar = self.getCalendarForId(id)
            calendar_slots = [[]] * len(slots)
            for event in calendar.objectValues('Event'):
                if event.transparent:
                    continue
                event_slots = event.getEventInSlots(
                    start_time, end_time, slots
                )
                i = 0
                for event_slot in event_slots:
                    if event_slot != None:
                        calendar_slot = calendar_slots[i]
                        allcal_slots = all_cal_slots[i]

                        calendar_slot[i] = slot_union(calendar_slot, event_slot)
                        allcal_slot[i] = slot_union(allcal_slot, event_slot)

                    i += 1

    security.declareProtected(View, 'getCalendarForId')
    def getCalendarForId(self, id):
        """Gets calendar for id, creates it if id is a user"""
        id = str(id)
        ids = self.objectIds()
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
    def getCalendarsDict(self):
        calendars_dict = {}
        for ob in self.objectValues('Calendar'):
            entry = calendars_dict.setdefault(ob.usertype, [])
            entry.append({
              'id': ob.id,
              'cn': ob.title_or_id(),
              'usertype': ob.usertype,
            })
        return calendars_dict

    security.declareProtected(View, 'getAttendeeInfo')
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

    security.declareProtected('Access contents information', 'get')
    def get(self, name, default=None):
        """
        """
        try:
            return self[name]
        except KeyError:
            return default

    def __getitem__(self, name):
        try:
            ob = Workgroup[name]
            return ob
        except KeyError:
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
    ob = Calendars(id, title, description)
    container = dispatcher.Destination()
    container._setObject(id, ob)
    #ob = container._getOb(id)
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
