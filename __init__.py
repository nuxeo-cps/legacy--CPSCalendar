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
from Products.CMFCore.permissions import AddPortalContent

#import Calendars
import Calendar
import Event
import CPSCalendarTool

tools = (
    CPSCalendarTool.CPSCalendarTool,
)

contentClasses = (
    #Calendars.Calendars,
    Calendar.Calendar,
    Event.Event,
)

contentConstructors = (
    #Calendars.addCalendars,
    Calendar.addCalendar,
    Event.addEvent,
    CPSCalendarTool.addCPSCalendarTool,
)

fti = (
    #Calendars.factory_type_information +
    Calendar.factory_type_information +
    Event.factory_type_information +
    ()
)

bases = contentClasses

this_module = sys.modules[__name__]
z_bases = utils.initializeBasesPhase1(bases, this_module)

registerDirectory('skins', globals())

def initialize(registrar):
    utils.ToolInit(
        'CPS Calendar Tool',
        tools = tools,
        product_name = 'CPSCalendar',
        icon = 'tool.png',
    ).initialize(registrar)

    utils.initializeBasesPhase2(z_bases, registrar)

    utils.ContentInit(
        'Calendars',
        content_types = contentClasses,
        permission = AddPortalContent, # XXX
        extra_constructors = contentConstructors,
        fti = fti,
    ).initialize(registrar)

    # icon
    #utils.registerIcon(Calendars.Calendars, 'calendars_icon.png', globals())
    utils.registerIcon(Calendar.Calendar, 'calendar_icon.png', globals())
    utils.registerIcon(Event.Event, 'event_icon.png', globals())
