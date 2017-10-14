#!/usr/bin/env python3

from sys import stderr

import MySQLdb


class DBHndlr(object):
    """MySql Database Handler"""
    DATABASE_NOT_FOUND = 1049

    def __init__(self, db_config, form_keys, cols):
        try:
            self.db = MySQLdb.connect(host=db_config.host, user=db_config.usrname, passwd=db_config.passwd, use_unicode=True)
        except MySQLdb.OperationalError as ex:
            print("DB login err. %s" % ex, file=stderr)
            exit()
        self.db.autocommit("on")
        self.cursor = self.db.cursor()
        self.cursor.execute("SET NAMES %s", (db_config.encoding, ))
        self.cursor.execute("SET CHARACTER SET %s", (db_config.encoding,))
        self.cursor.execute("SET character_set_connection=%s", (db_config.encoding,))
        try:
            self.cursor.execute("use %s;" % (db_config.db_name,))
        except MySQLdb.OperationalError as ex:
            if ex.args[0] == self.__class__.DATABASE_NOT_FOUND:
                print("DB not found.\nCreating db %s..." % db_config.db_name)
                self.cursor.execute("create database %s character set %s;" % (db_config.db_name, db_config.encoding))
                self.cursor.execute("use %s;" % (db_config.db_name,))
            else:
                raise
        self.cursor.execute("show tables;")
        tbls = [i[0] for i in self.cursor.fetchall()]
        if db_config.tbl_name not in tbls:
            cols_str = "%s %s not null PRIMARY KEY" % (db_config.primary_key, "bigint")
            cols_str += ", %s %s" % (db_config.status_key, "int")
            for col in cols:
                cols_str += ", %s %s" % (col[form_keys.db_key], col[form_keys.db_type])
            self.cursor.execute("create table %s (%s);" % (db_config.tbl_name, cols_str))
        self.config = db_config

    def __del__(self):
        self.db.close()

    def get_cursor(self):
        return self.cursor

    def get_db(self):
        return self.db
