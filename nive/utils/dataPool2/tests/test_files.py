

import copy, time, StringIO
import unittest
from pkg_resources import resource_filename

from nive.utils.dataPool2.files import File


class fileentrytest(object):
    test=1
    
    @property
    def root(self):
        return resource_filename('nive.utils.dataPool2', 'tests/')
    
    @property
    def pool(self):
        return self
    
    def _Path(self, file):
        root = resource_filename('nive.utils.dataPool2', 'tests/')
        return root+"test_files.py"


class FileTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_create(self):
        #   File( filekey="", 
        #         filename="", 
        #         file=None, 
        #         size=0, 
        #         path="", 
        #         extension="", 
        #         fileid=0, 
        #         uid="", 
        #         tempfile=False, 
        #         filedict=None, 
        #         fileentry=None)
        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file="0123456789"
                    )
        self.assert_(file.filekey=="aaa")
        self.assert_(file.filename=="qqqq.png")
        self.assert_(file.size==10)
        self.assert_(file.extension=="png")

        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file="0123456789",
                    fileentry=fileentrytest()
                    )
        self.assert_(file.filekey=="aaa")
        self.assert_(file.filename=="qqqq.png")
        self.assert_(file.size==10)
        self.assert_(file.extension=="png")

        file = File(filekey="aaa",
                    path="/tmp/qqqq.png" 
                    )
        self.assert_(file.filekey=="aaa")
        self.assert_(file.filename=="qqqq.png")
        self.assert_(file.extension=="png")
        
        file = File(filedict={"filekey":"aaa",
                              "filename":"qqqq.png", 
                              "file":"0123456789",
                              "fileentry":fileentrytest()}
                    )
        self.assert_(file.filekey=="aaa")
        self.assert_(file.filename=="qqqq.png")
        self.assert_(file.size==10)
        self.assert_(file.extension=="png")


    def test_read(self):
        file = File("aaa", filename="import.zip", tempfile=True)
        self.assert_(file.isTempFile())
        self.assert_(file.filename=="import.zip")
        self.assert_(file.extension=="zip")
        self.assertRaises(IOError, file.read)

        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file="0123456789",
                    fileentry=fileentrytest()
                    )
        self.assert_(file.read()=="0123456789")

        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file="0123456789",
                    fileentry=fileentrytest()
                    )
        self.assert_(file.read(5)=="01234")
        self.assert_(file.read(5)=="56789")
        self.assert_(file.read(5)=="")
        self.assert_(file.tell()==10)
        file.seek(0)
        self.assert_(file.tell()==0)

        file = File(filekey="aaa",
                    file=None,
                    fileentry=fileentrytest()
                    )
        self.assertRaises(IOError, file.read)
        file.close()
        self.assertFalse(file.isTempFile())


    def test_path(self):
        root = resource_filename('nive.utils.dataPool2', 'tests/')
        file = File("aaa")
        file.fromPath(root+"test_db.py")
        self.assert_(file.filename=="test_db.py")
        self.assert_(file.extension=="py")
        self.assertFalse(file.abspath())

        file = File(filekey="aaa",
                    file=None
                    )
        file.fileentry=fileentrytest
        file.path = root+"test_db.py"
        self.assert_(file.abspath().startswith(root))
        
        file = File("aaa", filename="qqqq.png", size=10)
        file.fromPath(root+"test_db.py")
        self.assert_(file.filename=="qqqq.png")
        self.assert_(file.extension=="png")
        
        
    def test_dict(self):
        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file="0123456789",
                    fileentry=fileentrytest()
                    )
        self.assert_(file.get("filekey")=="aaa")
        self.assert_(file.get("filename")=="qqqq.png")
        self.assert_(file.get("size")==10)

        self.assert_(file["filekey"]=="aaa")
        self.assert_(file["filename"]=="qqqq.png")
        self.assert_(file["size"]==10)

        self.assert_(file.get("none",123)==123)
        
        file.update({"filekey":"bbb", "filename":"oooo.png"})
        self.assert_(file.get("filekey")=="bbb")
        self.assert_(file.get("filename")=="oooo.png")
        
        for k in file:
            self.assert_(k)
