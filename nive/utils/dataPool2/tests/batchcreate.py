

import copy

import test_MySql
try:
    from nive.utils.dataPool2.mySqlPool import *
except:
    pass

import test_db
from nive.utils.dataPool2.sqlite3Pool import *


def create_mysql(n):
    pool = MySql(test_MySql.conf)
    pool.SetStdMeta(copy.copy(test_MySql.stdMeta))
    pool.GetPoolStructureObj().SetStructure(test_MySql.struct)
    pool.CreateConnection(test_MySql.conn)

    print "Create", n, "entries (data+meta+file): ",
    t = time.time()
    for i in range(0,n):
        e=pool.CreateEntry(u"data1")
        if i==0:  id = e.GetID()
        e.data.update(test_MySql.data1_1)
        e.meta.update(test_MySql.meta1)
        e.CommitFile(u"file1", {"file":test_db.file1_1, "filename":"file1.txt"})
        #e.Commit()
    t2 = time.time()

    pool.Close()
    print n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry"
    print
    return id


def create_sqlite3(n):
    pool = Sqlite3(test_db.conf)
    pool.SetStdMeta(copy.copy(test_db.stdMeta))
    pool.GetPoolStructureObj().SetStructure(test_db.struct)
    pool.CreateConnection(test_db.conn)

    print "Create", n, "entries (data+meta+file): ",
    t = time.time()
    for i in range(0,n):
        e=pool.CreateEntry(u"data1")
        if i==0:  id = e.GetID()
        e.data.update(test_db.data1_1)
        e.meta.update(test_db.meta1)
        e.CommitFile(u"file1", {"file":test_db.file1_1, "filename":"file1.txt"})
        e.Commit()
    t2 = time.time()

    pool.Close()
    print n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry"
    print
    return id



# ----------------------------------------------------------------------------------------------

def run():
    n = 1 * 500
    #id = create_mysql(n)
    id = create_sqlite3(n)


if __name__ == '__main__':
    run()
