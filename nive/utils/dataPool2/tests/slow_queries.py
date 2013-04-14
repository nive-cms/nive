

import copy

import test_MySql
try:
    from nive.utils.dataPool2.mySqlPool import *
except:
    pass



def sqlquery4(n):
    pool = MySql(test_MySql.conf)
    pool.SetStdMeta(copy.copy(test_MySql.stdMeta))
    pool.GetPoolStructureObj().SetStructure(test_MySql.struct)
    pool.CreateConnection(test_MySql.conn)

    print "SQL Query filename (text index) result=all, sort=filename, operator=like: ",
    t = time.time()
    for i in range(0,n):
        files = pool.SearchFiles({u"filename": u"file1.txt"}, sort=u"filename", operators={u"fielname":u"like"})
    t2 = time.time()

    pool.Close()
    print n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement"
    print

def sqlquery5(n):
    pool = MySql(test_MySql.conf)
    pool.SetStdMeta(copy.copy(test_MySql.stdMeta))
    pool.GetPoolStructureObj().SetStructure(test_MySql.struct)
    pool.CreateConnection(test_MySql.conn)

    print "SQL Query filename (text index), result=all, sort=id, operator==: ",
    t = time.time()
    for i in range(0,n):
        files = pool.SearchFiles({u"filename": u"file1.txt"}, sort=u"id", operators={u"fielname":u"="})
    t2 = time.time()

    pool.Close()
    print n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement"
    print

def sqlquery6(n):
    pool = MySql(test_MySql.conf)
    pool.SetStdMeta(copy.copy(test_MySql.stdMeta))
    pool.GetPoolStructureObj().SetStructure(test_MySql.struct)
    pool.CreateConnection(test_MySql.conn)

    print "SQL Query filename (text index) no result: ",
    t = time.time()
    for i in range(0,n):
        files = pool.SearchFiles({u"filename": u"filexxx.txt"}, sort=u"filename", operators={u"fielname":u"like"})
    t2 = time.time()

    pool.Close()
    print n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement"
    print






def run():
    n = 100
    sqlquery4(n)
    sqlquery5(n)
    sqlquery6(n)




if __name__ == '__main__':
    run()
