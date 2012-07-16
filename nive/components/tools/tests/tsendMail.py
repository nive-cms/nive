
import time
import unittest
from smtplib import SMTPServerDisconnected

from nive.definitions import *
from nive.components.tools.sendMail import *

from nive.tests import db_app


from nive.helper import FormatConfTestFailure



# -----------------------------------------------------------------

class SendMailTest1(unittest.TestCase):


    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_tool(self):
        sendMail(configuration,None)
        
        
class SendMailTest2_db(unittest.TestCase):

    def setUp(self):
        self.app = db_app.app_db()
        self.app.Include(configuration)
    
    def tearDown(self):
        self.app.Close()


    def test_tool(self):
        t = self.app.GetTool("sendMail")
        self.assert_(t)

    
    def test_toolrun1(self):
        t = self.app.GetTool("sendMail")
        self.assert_(t)
        r,v = t()
        self.assertFalse(r)


    def test_toolrun2(self):
        t = self.app.GetTool("sendMail")
        self.assert_(t)
        try:
            r,v = t(recvmails=[("test@aaaaaaaa.com", "No name")], title="Testmail", body="body mail")
        except SMTPServerDisconnected:
            pass

if __name__ == '__main__':
    unittest.main()
