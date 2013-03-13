# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import *
from nive.security import *
from nive.helper import FormatConfTestFailure

from nive.cms.cmsview import view
from nive.cms.cmsview import cmsroot




class TestConf(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_conf1(self):
        r=view.configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_conf2(self):
        r=cmsroot.configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")


if __name__ == '__main__':
    unittest.main()
