# Copyright (c) 2002-2004 Nuxeo SARL <http://nuxeo.com>
# Copyright (c) 2002 CIRB, Belgique
# Authors: Julien Jalon <mailto:jj@nuxeo.com>
#          Lennart Regebro <mailto:lr@nuxeo.com>
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

"""
  CPSEvent
"""
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CPSCore.CPSBase import CPSBase_adder
from Products.CPSDocument.CPSDocument import CPSDocument
from Event import Event

factory_type_information  = ({
    'title': 'cpsevent',
    'description': 'This is a test. And this is the meaning of the test.',
    'content_icon': 'event_icon.gif',
    'content_meta_type': "CPS Event",
    'product': 'CPSCalendar',
    'factory': 'addCPSEvent',
    'immediate_view': 'cpsdocument_view',
    'global_allow': 1,
    'filter_content_types': 1,
    'allowed_content_types': [],
    'allow_discussion': 0,
    'cps_is_searchable': 1,
    'cps_proxy_type': 'document',
    'cps_display_as_document_in_listing': 0,
    'schemas': ['metadata', 'common', 'event'],
    'layouts': ['common', 'event'],
    'flexible_layouts': [],
    'storage_methods': [],
},)

class CPSEvent(CPSDocument, Event):
    """Collector Document"""

    meta_type = "CPS Event"

    security = ClassSecurityInfo()

    def matchesTime(self, start, stop):
        #import pdb;pdb.set_trace()
        event_start, event_stop = self.start, self.end
        if event_stop > start and event_start < stop:
            return 1
        return 0

    def getEventInSlots(self, start_time, end_time, slots):
        """
        """
        return self._standardMatch(start_time, end_time, slots,
               self.start, self.end)


InitializeClass(CPSEvent)

def addCPSEvent(dispatcher, id, REQUEST=None, **kw):
    """Add a Collector Document"""
    ob = CPSEvent(id, **kw)
    return CPSBase_adder(dispatcher, ob, REQUEST=REQUEST)

