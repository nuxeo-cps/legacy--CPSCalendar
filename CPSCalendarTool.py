# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Encolpe Degoute <edegoute@nuxeo.com>
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


from Products.CMFCore.PortalFolder import PortalFolder

from Products.CMFCore.CMFCorePermissions import setDefaultRoles
from Products.CMFCore.CMFCorePermissions import View
from Products.CMFCore.CMFCorePermissions import ManagePortal
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent
from Products.CMFCore.CMFCorePermissions import ViewManagementScreens
from Products.CMFCore.utils import SimpleItemWithProperties
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from AccessControl import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager

ManageWorkspaces = 'Manage Workspaces'
setDefaultRoles(ManageWorkspaces, ('Manager',))


WorkspaceManager = 'WorkspaceManager'
WorkspaceMember = 'WorkspaceMember'
WorkspaceVisitor = 'WorkspaceVisitor'
WorkspaceManagerRoles = (WorkspaceManager, WorkspaceMember, WorkspaceVisitor,)
WorkspaceMemberRoles = (WorkspaceMember, WorkspaceVisitor,)
WorkspaceVisitorRoles = (WorkspaceVisitor,)


def _cmpEv(a, b):
    return cmp(b['start'], a['start'])

def _slotUnion(cal_slot, with_free=0):
    result = []
    if not cal_slot:
        return []
    cal_slot = cal_slot[:]
    cal_slot.sort(_cmpEv)
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


class CPSCalendarTool(UniqueObject, PortalFolder):
    """
    This tool give the access to the collaborative side of CPSCalendar.
    
    It contains all the methods needed by Calendars object to find the others
    and process meeting or superpose calendars.
    """

    id = 'portal_adv_calendar'
    meta_type = 'CPS Advanced Calendar Tool'
    title = 'Advanced Calendar Tool'

    security = ClassSecurityInfo()

    manage_options = (ActionProviderBase.manage_options +
                      PortalFolder.manage_options[:1] +
                      PortalFolder.manage_options[2:])

    _actions = ()

    _properties = ({'id':'title', 'type':'string'},
                   {'id':'description', 'type':'text'},
                   )

    def __init__(self):
        PortalFolder.__init__(self, self.id)

    security.declareProtected('View', 'getCalendarObjects')
    def getCalendarObjects(self):
        """ return all available Calendar objects in a list
        """
        brains = self.portal_catalog.searchResults(meta_type='Calendar')
        result = []
        if brains == None:
            return result
        for brain in brains:
            result.append(brain.getObject())
        return result

    security.declareProtected('View', 'getCalendarIds')
    def getCalendarIds(self):
        """ return all available Calendar ids in a list
        """
        brains = self.portal_catalog.searchResults(meta_type='Calendar')
        result = []
        if brains == None:
            return result
        for brain in brains:
            result.append(brain.getId())
        return result

    security.declareProtected(View, 'getCalendarsDict')
    def getCalendarsDict(self, exclude=None):
        """ Return a short summary of all calendars
            It's used in meeting preparation to have all possibles attendees
        """
        calendars_dict = {}
        for ob in self.getCalendarObjects():
            entry = calendars_dict.setdefault(ob.usertype, [])
            if exclude is None or exclude != ob.id:
                entry.append({
                  'id': ob.id,
                  'cn': ob.title_or_id(),
                  'usertype': ob.usertype,
                  'path': ob.absolute_url(relative=1),
                  'url': ob.absolute_url(),
                })
        return calendars_dict

    # XXX use a special permission here
    security.declareProtected('View', 'unionCals')
    def unionCals(self, *cals, **kw):
        if not cals:
            return []
        if kw.get('with_free'):
            with_free = 1
        else:
            with_free = 0 # XXX: is with_free always set to 1 ?
        result = []
        length = len(cals[0])
        for i in range(length):
            this_slot = []
            for cal in cals:
                this_slot.extend(cal[i])
            result.append(_slotUnion(this_slot, with_free=with_free))
        return result

    security.declareProtected('View', 'getFreeBusy')
    def getFreeBusy(self, attendees, from_date, to_date,
                    from_time_hour, from_time_minute,
                    to_time_hour, to_time_minute):
        """Gets free/busy informations on attendees calendars"""
        # normalize
        start_time = DateTime(from_date.year(), from_date.month(),
                              from_date.day())
        to_date = to_date + 1
        end_time = DateTime(to_date.year(), to_date.month(), to_date.day())
        slot_start = start_time
        slots = []
        while slot_start.lessThan(end_time):
            slots.append((slot_start, slot_start+1))
            slot_start += 1
            slot_start = DateTime(slot_start.year(), slot_start.month(),
                                  slot_start.day())

        length = len(slots)

        # first create the mask calendar
        mask_cal = []
        if ((to_time_hour or to_time_minute) and
            (from_time_hour > to_time_hour or
                (from_time_hour == to_time_hour and
                    from_time_minute > to_time_minute))):
            from_time_hour, to_time_hour = to_time_hour, from_time_hour
            from_time_minute, to_time_minute = to_time_minute, from_time_minute

        for slot in slots:
            this_day = []
            date = slot[0]
            year = date.year()
            month = date.month()
            day = date.day()
            if from_time_hour or from_time_minute:
                mask_from = DateTime(year, month, day,
                                     from_time_hour, from_time_minute)
                this_day.append({
                    'start': date,
                    'stop': mask_from,
                })

            if to_time_hour or to_time_minute:
                mask_to = DateTime(year, month, day,
                                   to_time_hour, to_time_minute)
                this_day.append({
                    'start': mask_to,
                    'stop': slot[1],
                })
            mask_cal.append(this_day)

        calendars = self.getCalendarObjects()
        ids = [id for id in attendees if id in ids]
        cals_dict = {}
        cal_users = {}
        for calendar in calendars:
            id = calendar.id
            cal_users[id] = self.getAttendeeInfo(id)['cn']
            calendar_slots = []
            for i in range(len(slots)):
                calendar_slots.append([])
            slots_done = [None] * length
            for event in calendar.objectValues('Event'):
                if event.transparent:
                    continue
                event_slots = event.getEventInSlots(
                    start_time, end_time, slots)
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
                    list.append(_slotUnion(cal_slot))
                i += 1

        return {
            'cal_users': cal_users,
            'cals_dict': cals_dict,
            'mask_cal': mask_cal,
            'slots': slots,
        }

    security.declareProtected('ModifyPortalContent', 'createUserCalendar')
    def createUserCalendar(self, id):
        """Create an user calendar"""
        id = str(id)
        ids = self.objectIds('Calendar')
        if id in ids:
            return getattr(self, id)

        context = aq_parent(aq_inner(self))
        dirtool = getToolByName(context, 'portal_metadirectories')
        mtool = getToolByName(context, 'portal_membership')
        ttool = getToolByName(context, 'portal_types')

        members = dirtool.members
        entry = members.getEntry(id)

        aclu = self.acl_users
        user = aclu.getUser(id).__of__(aclu)

        if entry:
            # create this calendar for this member
            #ttool = getToolByName(context, 'portal_types')
            wtool = getToolByName(context, 'portal_workflow')

            # Setup a temporary security manager so that creation is not
            # hampered by insufficient roles.
            old_user = getSecurityManager().getUser()
            # Use member_id so that the Owner role is set for it
            tmp_user = CPSUnrestrictedUser(id, '',
                                           ['Manager', 'Member'], '')
            tmp_user = tmp_user.__of__(aclu)
            newSecurityManager(None, tmp_user)

            wtool.invokeFactoryFor(self, 'Calendar', id,
                                   title=entry['fullname'],
                                   description='')

            calendar_type_info = ttool.getTypeInfo('Calendar')

            ob = self._getOb(id)
            ob._computedtitle = 1
            calendar_type_info._finishConstruction(ob)
 
            # Grant ownership to Member
            try:
                ob.changeOwnership(user)
                # XXX this method is defined in a testcase and just does a pass
            except AttributeError:
                pass  # Zope 2.1.x compatibility

            ob.manage_setLocalRoles(id, ['Owner', 'WorkspaceManager'])

            # Rebuild the tree with corrected local roles.
            # This needs a user that can View the object.
            portal_eventservice = getToolByName(self, 'portal_eventservice')
            portal_eventservice.notify('sys_modify_security', ob, {})

            newSecurityManager(None, old_user)
            return ob
        else:
            return None

    security.declareProtected(View, 'getAttendeeInfo')
    def getAttendeeInfo(self, id, status=0):
        """ get info from others attendees of one event.
        attendees are other calendars.

        return a dictionnary with cn, id, usertype and status.
        """
        if id in self.getCalendarIds():
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
        """ return the list of all Calendar objects visible by the user
        """
        mtool = getToolByName(self, 'portal_membership')
        cals = []
        for cal in self.getCalendarObjects():
            if mtool.checkPermission('List folder contents', cal):
                cals.append(cal)
        return cals