import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from DateTime.DateTime import DateTime
from Products.CPSCalendar.CPSCalendarTool import stringToDateTime


class TestStringToDateTime(unittest.TestCase):

    def testWithSeparators(self):
                                                    #Selection process
        date = stringToDateTime('01/02/03')
        self.assertEquals(date, DateTime(2003,1,2)) #Any: Defaults to US
        date = stringToDateTime('13/01/01')
        self.assertEquals(date, DateTime(2001,1,13))#Must be EU
        date = stringToDateTime('01/13/02')
        self.assertEquals(date, DateTime(2002,1,13))#Intl or EU, EU comes first
        date = stringToDateTime('01/01/13')
        self.assertEquals(date, DateTime(2013,1,1)) #Any: Defaults to US
        date = stringToDateTime('33/01/02')
        self.assertEquals(date, DateTime(2033,1,2)) #Must be Intl
        date = stringToDateTime('01/02/33')
        self.assertEquals(date, DateTime(2033,1,2)) #EU/US, Defaults to US
        date = stringToDateTime('13/01/33')
        self.assertEquals(date, DateTime(2033,1,13))#Must be EU
        date = stringToDateTime('01/13/33')
        self.assertEquals(date, DateTime(2033,1,13))#Must be US
        date = stringToDateTime('33/01/13')
        self.assertEquals(date, DateTime(2033,1,13))#Must be Intl
        date = stringToDateTime('13/01/13')
        self.assertEquals(date, DateTime(2013,1,13))#Intl or EU, EU default
        date = stringToDateTime('01/13/13')
        self.assertEquals(date, DateTime(2013,1,13))#Must be US
        
    def testWithoutSeparators(self):
        date = stringToDateTime('330113')
        self.assertEquals(date, DateTime(2033,1,13))#Must be Intl
        date = stringToDateTime('20330113')
        self.assertEquals(date, DateTime(2033,1,13))#Must be Intl

    def testInvalidDates(self):
        self.assertRaises(ValueError, stringToDateTime,'01/33/01')
        self.assertRaises(ValueError, stringToDateTime,'13/33/01')
        self.assertRaises(ValueError, stringToDateTime,'33/13/01')
        self.assertRaises(ValueError, stringToDateTime,'01/33/13')
        self.assertRaises(ValueError, stringToDateTime,'13/13/01')
        self.assertRaises(ValueError, stringToDateTime,'33/33/01')
        self.assertRaises(ValueError, stringToDateTime,'33/01/33')
        self.assertRaises(ValueError, stringToDateTime,'01/33/33')
        self.assertRaises(ValueError, stringToDateTime,'13/13/13')
        self.assertRaises(ValueError, stringToDateTime,'33/01/33')
        self.assertRaises(ValueError, stringToDateTime,'03012005')
 

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStringToDateTime))
    return suite

