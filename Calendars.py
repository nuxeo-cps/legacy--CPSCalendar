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
            entry = calendars_dict.get(ob.usertype, None)
            if entry is None:
                calendars_dict[ob.usertype] = entry = []
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

    def __getitem__(self, name):
        try:
            ob = Workgroup.__getitem__(self, name)
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
