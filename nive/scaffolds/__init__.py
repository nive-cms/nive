import binascii
import os
import getpass

from pyramid.compat import native_

from pyramid.scaffolds import PyramidTemplate # API
from pyramid.scaffolds.template import Template

class DefaultSqliteTemplate(PyramidTemplate):
    _template_dir = 'defaultSqlite'
    summary = 'A simple nive website with Sqlite database'

    def pre(self, command, output_dir, vars):
        """ Overrides :meth:`pyramid.scaffold.template.Template.pre`, adding
        several variables to the default variables list (including
        ``random_string``, and ``package_logger``).  It also prevents common
        misnamings (such as naming a package "site" or naming a package
        logger "root".
        """
        # configuration
        user = None
        while not user:
            user = raw_input("Admin username: ")
        vars['adminuser'] = user
    
        pprompt = lambda: (getpass.getpass('Password: '), getpass.getpass('Retype password: '))
    
        p1, p2 = pprompt()
        while p1 != p2:
            print('Passwords do not match. Try again')
            p1, p2 = pprompt()
        
        vars['adminuser'] = user
        vars['adminpass'] = p1
        
        vars['language'] = raw_input("Locale name. Please choose english-> en or german-> de: ")

        return PyramidTemplate.pre(self, command, output_dir, vars)
    
    
class DefaultMysqlTemplate(PyramidTemplate):
    _template_dir = 'defaultMysql'
    summary = 'A simple nive website with MySql database'

    def pre(self, command, output_dir, vars):
        """ Overrides :meth:`pyramid.scaffold.template.Template.pre`, adding
        several variables to the default variables list (including
        ``random_string``, and ``package_logger``).  It also prevents common
        misnamings (such as naming a package "site" or naming a package
        logger "root".
        """
        # configuration
        user = None
        while not user:
            user = raw_input("Admin username: ")
        vars['adminuser'] = user
        
        pprompt = lambda: (getpass.getpass('Password: '), getpass.getpass('Retype password: '))
    
        p1, p2 = pprompt()
        while p1 != p2:
            print('Passwords do not match. Try again')
            p1, p2 = pprompt()
            
        vars['adminpass'] = p1
        
        print "Please enter MySql database settings for the website. Two databases will be created, one for website contents ",
        print "and one to store userdata. Host, port, user and password are used for both databases."
        print ""
        
        vars['dbcontentname'] = raw_input("Content database name (default %s): " % vars["project"])
        if not vars['dbcontentname']:
            vars['dbcontentname'] = vars["project"]
        vars['dbusername'] = raw_input("User database name (default %s_user): "% vars["project"])
        if not vars['dbusername']:
            vars['dbusername'] = vars["project"]+"_user"
        vars['dbhost'] = raw_input("MySql database host (default localhost): ")
        vars['dbport'] = raw_input("MySql database port (leave empty to use default): ")
        vars['dbuser'] = raw_input("MySql database user: ")
            
        pprompt = lambda: (getpass.getpass('Password: '), getpass.getpass('Retype password: '))
    
        p1, p2 = pprompt()
        while p1 != p2:
            print('Passwords do not match. Try again')
            p1, p2 = pprompt()

        vars['dbpass'] = p1
        
        vars['language'] = raw_input("Locale name. Please choose english-> en or german-> de: ")

        return PyramidTemplate.pre(self, command, output_dir, vars)
