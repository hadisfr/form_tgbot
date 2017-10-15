#!/usr/bin/env python3

from time import time
from sys import stderr

import MySQLdb

from dict_wrapper import DictWrapper


class DBHndlr(object):
    """MySql Database Handler"""

    DATABASE_NOT_FOUND = 1049
    DUPLICATE_KEY = 1062

    ROW_NOT_FOUND_STAT = -1

    class CellNotFound(MySQLdb.DatabaseError):
        """database cell not found excpetion.

        inherited from MySQLdb.DatabaseError.
        """
        def __init__(self, *args, **argv):
            super().__init__(*args, **argv)

    def __init__(self, db_config, form_keys, cols):
        try:
            self.db = MySQLdb.connect(
                host=db_config.host,
                user=db_config.usrname,
                passwd=db_config.passwd,
                use_unicode=True)
        except MySQLdb.OperationalError as ex:
            print("DB login err. %s" % ex, file=stderr)
            exit()
        self.db.autocommit("on")
        self.cursor = self.db.cursor()
        self.cursor.execute("SET NAMES %s", (db_config.encoding, ))
        self.cursor.execute("SET CHARACTER SET %s", (db_config.encoding,))
        self.cursor.execute("SET character_set_connection = %s", (db_config.encoding,))
        try:
            self.cursor.execute("use %s;" % (db_config.db_name,))
        except MySQLdb.OperationalError as ex:
            if ex.args[0] == self.__class__.DATABASE_NOT_FOUND:
                print("DB not found.\nCreating db %s..." % db_config.db_name, file=stderr)
                self.cursor.execute(
                    "create database %s character set %s;" % (
                        db_config.db_name,
                        db_config.encoding))
                self.cursor.execute("use %s;" % (db_config.db_name,))
            else:
                raise

        self.cursor.execute("show tables;")
        tbls = [i[0] for i in self.cursor.fetchall()]
        if db_config.tbl_name not in tbls:
            print("Table not found.\nCreating table %s..." % db_config.tbl_name, file=stderr)
            cols_str = "%s %s not null PRIMARY KEY" % (db_config.primary_key, "bigint")
            cols_str += ", %s %s not null" % (db_config.status_key, "int")
            cols_str += ", %s %s not null" % (db_config.timestamp_key, "int")
            for col in cols:
                cols_str += ", %s %s" % (col[form_keys.db_key], col[form_keys.db_type])
            self.cursor.execute("create table %s (%s);" % (db_config.tbl_name, cols_str))
        self.config = db_config

    def __del__(self):
        try:
            self.db.close()
        except AttributeError:
            pass

    def get_cursor(self):
        return self.cursor

    def get_db(self):
        return self.db

    def existed(self, uid):
        return bool(self.cursor.execute(
            "select * from %s where %s = %s" % (
                self.config.tbl_name,
                self.config.primary_key,
                "%s"),
            (uid,)))

    def create_row(self, uid):
        try:
            return self.cursor.execute(
                "insert into %s (%s, %s, %s) values(%s, %s, %s);" % (
                    self.config.tbl_name,
                    self.config.primary_key,
                    self.config.status_key,
                    self.config.timestamp_key,
                    "%s",
                    "%s",
                    "%s"),
                (uid, 0, int(time())))
        except MySQLdb.DatabaseError as ex:
            if ex.args[0] == self.__class__.DUPLICATE_KEY:
                print("ERR: Duplicate UID. %s" % ex, file=stderr)
                return 0
            else:
                raise

    def get_attr(self, uid, key):
        if self.cursor.execute(
                "select %s from %s where %s = %s" % (
                    key,
                    self.config.tbl_name,
                    self.config.primary_key,
                    "%s"),
                (uid,)):
            return self.cursor.fetchone()[0]
        else:
            raise self.CellNotFound()

    def set_attr(self, uid, key, val):
        if not self.existed(uid):
            self.create_row(uid)
        try:
            return self.cursor.execute(
                "update %s set %s = %s, %s = %s where %s = %s;" % (
                    self.config.tbl_name,
                    key,
                    "%s",
                    self.config.timestamp_key,
                    "%s",
                    self.config.primary_key,
                    "%s"),
                (val, int(time()), uid))
        except MySQLdb.DatabaseError as ex:
            print("ERR: %s" % ex, file=stderr)
            return 0

    def get_status(self, uid):
        try:
            return self.get_attr(uid, self.config.status_key)
        except self.CellNotFound:
            return self.__class__.ROW_NOT_FOUND_STAT

    def set_status(self, uid, status):
        return self.set_attr(uid, self.config.status_key, status)
