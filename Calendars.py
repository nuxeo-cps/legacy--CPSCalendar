# (c) 2002 Nuxeo SARL <http://nuxeo.com>
# (c) 2002 Florent Guillaume <mailto:fg@nuxeo.com>
# (c) 2002 Préfecture du Bas-Rhin, France
# See license info at the end of this file.
# $Id$

"""
  Calendars container
"""

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

from Products.CMFCore.CMFCorePermissions import \
     View, ManageProperties

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

    _properties = ({'id':'title', 'type':'string'},
                   {'id':'description', 'type':'text'},
                   )

    isDocumentContainer = 0

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
