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
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Acquisition import aq_inner, aq_parent

from Products.CMFCore.CMFCorePermissions import \
     View, ManageProperties

from Products.NuxWorkgroup.Workgroup import Workgroup, ManageWorkgroups

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
                  },
                 {'id': 'localroles',
                  'name': '_action_access_rights_',
                  'action': 'workgroup_localrole_form',
                  'permissions': (ManageWorkgroups,),
                  'category': 'object'
                  },
                 {'id': 'addevent',
                  'name': '_action_addevent_',
                  'action': 'calendar_addevent_form',
                  'permissions': ("Add portal content",),
                  'category': 'object'
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

    _pending_events = ()

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
        LOG('NGCal', DEBUG, 'add pending event %s for %s' % (event_dict, self.id))
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
                LOG('NGCal', DEBUG, 'Appending to already pending event')
                event_dict['change'] = this_event['change'] + event_dict['change']
            else:
                LOG('NGCal', DEBUG, 'Creating this pending event: %s' % (event_dict, ))
        events.append(event_dict)
        self._pending_events = tuple(events)
        self._notifyMembers(base_dict)

    security.declareProtected('Add portal content', 'confirmPendingEvent')
    def confirmPendingEvent(self, event_id, REQUEST=None, **kw):
        """
        """
        if REQUEST is not None:
            kw.update(REQUEST.form)
        LOG('NGCal', DEBUG, 'Confirming %s with %s' % (event_id, kw))
        pending = None
        for event in self._pending_events:
            if event['id'] == event_id:
                pending = event
                break
        if event is None:
            LOG('NGCal', DEBUG, "Can't locate pending event %s" % (event_id, ))
            return
        request = pending['request']
        if request == 'request':
            LOG('NGCal', DEBUG, 'Ok?')
            status = kw.get('status')
            LOG('NGCal', DEBUG, 'Ok!')
            event = getattr(self, event_id, None)
            if event is None:
                self.invokeFactory('Event', **pending['event'])
                event = getattr(self, event_id)
            else:
                LOG('NGCal', DEBUG, 'edit event %s with: %s' % (event, pending['event'], ))
                kw = pending['event']
                event.edit(**kw)
            if status is not None:
                event.setMyStatus(status)
        elif request == 'status':
            event = getattr(self, event_id, None)
            if event is None:
                LOG('NGCal', DEBUG, "Can't locate event %s" % (event_id, ))
                return
            for change in pending['change']:
                LOG('NGCal', DEBUG, "Changing %s" % (change, ))
                event.setAttendeeStatus(change['attendee'], change['status'])
        events = [event for event in self._pending_events if event['id'] != event_id]
        self._pending_events = tuple(events)
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect("%s/%s" % (self.absolute_url(), event_id))

    security.declareProtected('Add portal content', 'cleanPendingEvents')
    def cleanPendingEvents(self, REQUEST=None):
        """
        """
        self._pending_events = ()
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

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

InitializeClass(Calendar)


def addCalendar(dispatcher, id,
                 title='',
                 description='',
                 usertype='member',
                 REQUEST=None):
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
