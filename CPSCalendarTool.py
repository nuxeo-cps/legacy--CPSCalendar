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

from zLOG import LOG, DEBUG
from Globals import InitializeClass
from DateTime import DateTime
from Products.CMFCore.PortalFolder import PortalFolder
from Products.CMFCore.CMFCorePermissions import setDefaultRoles
from Products.CMFCore.CMFCorePermissions import View
from Products.CMFCore.CMFCorePermissions import ManagePortal
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from AccessControl import ClassSecurityInfo

ManageWorkspaces = 'Manage Workspaces'
setDefaultRoles(ManageWorkspaces, ('Manager',))


WorkspaceManager = 'WorkspaceManager'
WorkspaceMember = 'WorkspaceMember'
WorkspaceVisitor = 'WorkspaceVisitor'
WorkspaceManagerRoles = (WorkspaceManager, WorkspaceMember, WorkspaceVisitor,)
WorkspaceMemberRoles = (WorkspaceMember, WorkspaceVisitor,)
WorkspaceVisitorRoles = (WorkspaceVisitor,)


def _cmpEv(a, b):
    """Compare cal_slot by start date"""
    return cmp(b['start'], a['start'])

def _slotUnion(cal_slot, with_free=0):
    """Calculate and fusion events' display information from cal_slot.

    with_free: give only free time
    """
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
    This tool gives access to the collaborative side of CPSCalendar.
    
    It contains all the methods needed by Calendars object to find the others
    and process meeting or superpose calendars.
    """

    id = 'portal_cpscalendar'
    meta_type = 'CPS Calendar Tool'
    title = 'CPS Calendar Tool'

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

    security.declareProtected('View', 'listCalendars')
    def listCalendars(self):
        """Return all available Calendar objects in a list"""
        brains = self.portal_catalog.searchResults(meta_type='Calendar')
        if brains:
            return [brain.getObject() for brain in brains]
        else:
            return []

    security.declareProtected('View', 'listCalendarPaths')
    def listCalendarPaths(self):
        """Return all available Calendars' paths in a list"""
        calendars = self.listCalendars()
        return [cal.getRpath() for cal in calendars]

    security.declareProtected('View', 'getCalendarPathForUser')
    def getCalendarPathForUser(self, user_id):
        """Return calendar (r)path for user"""
        mtool = getToolByName(self, 'portal_membership')
        utool = getToolByName(self, 'portal_url')
        return mtool.getHomeUrl(user_id)[len(utool())+1:] + '/calendar'

    security.declareProtected('View', 'getCalendarForUser')
    def getCalendarForUser(self, user_id):
        """Get calendar for user <user_id>"""
        return self.getCalendarForPath(self.getCalendarPathForUser(user_id))

    security.declareProtected(View, 'getCalendarsDict')
    def getCalendarsDict(self, exclude=''):
        """Return a short summary of all calendars

        It's used in meeting preparation to have all possible attendees

        exclude: one calendar rpath to remove of the list
        """
        calendars_dict = {}
        for calendar in self.listCalendars():
            entry = calendars_dict.setdefault(calendar.usertype, [])
            rpath = calendar.getRpath()
            if exclude != rpath:
                entry.append({
                  'id': calendar.id,
                  'cn': calendar.title_or_id(),
                  'usertype': calendar.usertype,
                  'rpath': rpath,
                  'owner': calendar.getOwnerId(),
                  'path': calendar.absolute_url(),
                })
        return calendars_dict

    security.declarePrivate('getCalendarForPath')
    def getCalendarForPath(self, rpath, unrestricted=0):
        """Return a calendar

        rpath: relative path for the calendar
        Return None if no calendar found
        """
        utool = getToolByName(self, 'portal_url')
        portal = utool.getPortalObject()
        try:
            if unrestricted:
                calendar = portal.unrestrictedTraverse(rpath)
            else:
                calendar = portal.restrictedTraverse(rpath)
            if calendar.meta_type != 'Calendar':
                raise KeyError
            return calendar
        except KeyError:
            return None

    # XXX use a special permission here
    security.declareProtected('View', 'listFreeSlots')
    def listFreeSlots(self, slot_list_list, with_free=0):
        """Return the list of free slot for the list cals

        slot_list_list: list of list of {'start': DateTime, 'stop': DateTime}
        dictionaries
        with_free: binary, calculate free time slot
        """
        if not slot_list_list:
            return []
        result = []
        length = len(slot_list_list[0])
        for i in range(length):
            this_slot = []
            for slot_list in slot_list_list:
                this_slot.extend(slot_list[i])
            result.append(_slotUnion(this_slot, with_free=with_free))
        return result

    security.declareProtected('View', 'getFreeBusy')
    def getFreeBusy(self, attendees, from_date, to_date,
                    from_time_hour, from_time_minute,
                    to_time_hour, to_time_minute):
        """Get free/busy informations on attendees calendars

        attendees: list of calendars
        """
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

        calendars = self.listCalendars()
        cals_dict = {}
        cal_users = {}
        for calendar in calendars:
            rpath = calendar.getRpath()
            if rpath not in attendees:
                continue
            cal_users[rpath] = self.getAttendeeInfo(rpath)['cn']
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
            cals_dict[rpath] = list = []
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

    security.declareProtected(ManagePortal, 'createMemberCalendar')
    def createMemberCalendar(self, member_id):
        # XXX: is member_id really necessary here ?
        """Create a calendar in the home folder of a member

        member_id: member's id for which we create this calendar

        Precondition: member_id must be a valid user id
        """
        mtool = getToolByName(self, 'portal_membership')
        ttool = getToolByName(self, 'portal_types')

        # XXX: use TranslationServices here
        mcat = self.Localizer.cpscalendar or (lambda x: unicode(x))

        context = mtool.getHomeFolder(member_id)

        aclu = self.acl_users
        user = aclu.getUser(member_id)
        assert user
        user = user.__of__(aclu)

        # create this calendar for this member
        title = mcat('cpscalendar_user_calendar_name_beg').encode('ISO-8859-15',
                                                                  'ignore')\
              + user.getUserName()\
              + mcat('cpscalendar_user_calendar_name_end').encode('ISO-8859-15',
                                                                  'ignore')
        #raise str(title)
        wtool = getToolByName(self, 'portal_workflow')
        wtool.invokeFactoryFor(context, 'Calendar', 'calendar',
                               title=title,
                               description='')

        calendar_type_info = ttool.getTypeInfo('Calendar')

        ob = context._getOb('calendar')
        calendar_type_info._finishConstruction(ob)
 
        # XXX: is this necessay ?
        # Grant ownership to Member
        ob.changeOwnership(user)

        ob.manage_setLocalRoles(member_id, ['Owner', 'WorkspaceManager'])

        # Rebuild the tree with corrected local roles.
        # This needs a user that can View the object.
        portal_eventservice = getToolByName(self, 'portal_eventservice')
        portal_eventservice.notify('sys_modify_security', ob, {})

    security.declareProtected(View, 'getAttendeeInfo')
    def getAttendeeInfo(self, rpath, status=0):
        """Get info from others attendees of one event.
        attendees are other calendars.

        Return a dictionary with cn, rpath, id, usertype and status.
        """
        id = rpath.split('/')[-1]
        calendar = self.getCalendarForPath(rpath, unrestricted=1)
        if calendar:
            info = {
                'id': id,
                'rpath': rpath,
                'usertype': calendar.usertype,
            }
            if calendar.usertype != 'member':
                info['cn'] = calendar.title_or_id()
            else:
                id = calendar.getOwnerId()
                dirtool = getToolByName(self, 'portal_metadirectories')
                members = dirtool.members
                entry = members.getEntry(id)
                if entry is None:
                    info['cn'] = id
                else:
                    info['cn'] = entry.get(members.display_prop, id)
        else:
            # Maybe a member with no created calendar
            dirtool = getToolByName(self, 'portal_metadirectories')
            members = dirtool.members
            entry = members.getEntry(id)
            if entry is None:
                return None
            else:
                info = {
                    'id': id,
                    'rpath': rpath,
                    'usertype': 'member',
                    'cn': entry.get(members.display_prop, id),
                }
        if status:
            info['status'] = 'unconfirmed'
        return info

    security.declareProtected('View', 'listVisibleCalendars')
    def listVisibleCalendars(self):
        """Return the list of all Calendar objects visible by the user"""
        mtool = getToolByName(self, 'portal_membership')
        cals = []
        for cal in self.listCalendars():
            if mtool.checkPermission('List folder contents', cal):
                cals.append(cal)
        return cals

InitializeClass(CPSCalendarTool)

def addCPSCalendarTool(container, REQUEST=None):
    """Add a CPS Calendar Tool."""
    ob = CPSCalendarTool()
    id = ob.getId()
    container._setObject(id, ob)
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(container.absolute_url()+'/manage_main')
