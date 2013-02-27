
import sys
WIN = sys.platform == "win32"

# sqlite and mysql
if WIN:
    ROOT = "c:\\Temp\\nive\\"
else:
    ROOT = "/var/tmp/nive/"

# mysql
HOST = "localhost"
PORT = ""
USER = "root"
DATABASE = "ut_nive"
PASSWORD = ""
