# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import *
from nive.security import *
from nive.helper import FormatConfTestFailure

from nive.userdb import app, root, user




class TestConf(unittest.TestCase):

    def test_conf1(self):
        r=app.configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_conf2(self):
        r=root.configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_conf3(self):
        r=user.configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

