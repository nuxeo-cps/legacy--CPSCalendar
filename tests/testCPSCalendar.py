#
# Test Zope's standard UserFolder
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

#os.environ['STUPID_LOG_FILE'] = os.path.join(os.getcwd(), 'zLOG.log')
#os.environ['STUPID_LOG_SEVERITY'] = '-200'  # DEBUG

from Testing import ZopeTestCase
from Testing.ZopeTestCase import _user_name, _user_role, _folder_name, _standard_permissions
from AccessControl import Unauthorized

from Products.CPSCalendar.Calendars import Calendars
from Products.CPSCalendar.Calendar import Calendar
from Products.CPSCalendar.Event import Event

_pm = 'ThePublishedMethod'


class TestBase(ZopeTestCase.ZopeTestCase):

    _setup_fixture = 0

# TODO: 


if __name__ == '__main__':
    framework(descriptions=0, verbosity=1)
else:
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestUserFolder))
        suite.addTest(unittest.makeSuite(TestAccess))
        suite.addTest(unittest.makeSuite(TestValidate))
        suite.addTest(unittest.makeSuite(TestPluginFolder))
        return suite
