from Testing import ZopeTestCase
from Products.CPSDefault.tests import CPSTestCase

ZopeTestCase.installProduct('CPSCalendar')
ZopeTestCase.installProduct('NuxMetaDirectories')

CPSTestCase.setupPortal()

class CPSCalendarTestCase(CPSTestCase.CPSTestCase):
    pass

