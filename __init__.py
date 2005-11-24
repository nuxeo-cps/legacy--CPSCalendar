# Copyright (c) 2002-2003 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <mailto:fg@nuxeo.com>
# See license info at the end of this file.
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

import sys

from Products.CMFCore import utils
from Products.CMFCore.DirectoryView import registerDirectory
try:
    from Products.CMFCore.permissions import AddPortalContent
except ImportError:
    # BBB until CPS 3.4.0 where we don't care about CMF 1.4 anymore
    from Products.CMFCore.CMFCorePermissions import AddPortalContent

import Calendar
import Event
import CPSCalendarTool

tools = (
    CPSCalendarTool.CPSCalendarTool,
)

contentClasses = (
    Calendar.Calendar,
    Event.Event,
)

contentConstructors = (
    Calendar.addCalendar,
    Event.addEvent,
    CPSCalendarTool.addCPSCalendarTool,
)

fti = (
    Calendar.factory_type_information +
    Event.factory_type_information +
    ()
)

registerDirectory('skins', globals())

def initialize(registrar):
    try:
        utils.ToolInit(
            meta_type='CPS Calendar Tool',
            tools = tools,
            icon = 'tool.png',
        ).initialize(registrar)
    except TypeError:
        # BBB: CMF 1.4.x
        utils.ToolInit(
            meta_type='CPS Calendar Tool',
            tools = tools,
            product_name='CPSCalendar', # BBB
            icon = 'tool.png',
        ).initialize(registrar)

    utils.ContentInit(
        'Calendars',
        content_types = contentClasses,
        permission = AddPortalContent, # XXX
        extra_constructors = contentConstructors,
        fti = fti,
    ).initialize(registrar)

    # icon
    utils.registerIcon(Calendar.Calendar, 'calendar_icon.png', globals())
    utils.registerIcon(Event.Event, 'event_icon.png', globals())
