#!/usr/bin/env python3

from time import time
from sys import stderr
from collections import OrderedDict

import sqlite3
from openpyxl import Workbook


class DBHndlr(object):
    """SQLite3 Database Handler"""

    DATABASE_NOT_FOUND = 1049
    DUPLICATE_KEY = 1062

    ROW_NOT_FOUND_STAT = -1

    class CellNotFound(sqlite3.Error):
        """database cell not found excpetion.

        inherited from sqlite3.Error.
        """
        def __init__(self, *args, **argv):
            super().__init__(*args, **argv)

    def __init__(self, db_config, form_keys, cols):
        self.url = db_config.url
        conn, cursor = self.get_conn()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tbls = [i[0] for i in cursor.fetchall()]
        if db_config.tbl_name not in tbls:
            print("Table not found.\nCreating table %s..." % db_config.tbl_name, file=stderr)
            cols_str = "%s %s not null PRIMARY KEY" % (db_config.primary_key, "bigint")
            cols_str += ", %s %s not null" % (db_config.status_key, "int")
            cols_str += ", %s %s not null" % (db_config.chat_key, "int")
            cols_str += ", %s %s" % (db_config.username_key, "text")
            cols_str += ", %s %s not null" % (db_config.timestamp_key, "int")
            for col in cols:
                cols_str += ", %s %s" % (col[form_keys.db_key], col[form_keys.db_type])
            cursor.execute("create table %s (%s);" % (db_config.tbl_name, cols_str))
        conn.commit()
        conn.close()
        self.config = db_config
        self.report_keys = OrderedDict((col[form_keys.db_key], col[form_keys.report_key]) for col in cols)

    def get_conn(self):
        try:
            conn = sqlite3.connect(self.url)
        except sqlite3.Error as ex:
            print("DB login err. %s" % ex, file=stderr)
            # exit()
        cursor = conn.cursor()
        cursor.execute("pragma encoding=utf8")
        return conn, cursor

    def existed(self, uid):
        conn, cursor = self.get_conn()
        cursor.execute(
            "select * from %s where %s = %s" % (
                self.config.tbl_name,
                self.config.primary_key,
                "?"),
            (uid,))
        res = bool(cursor.fetchone())
        conn.close()
        return res

    def create_row(self, uid, chat_id):
        try:
            conn, cursor = self.get_conn()
            cursor.execute(
                "insert into %s (%s, %s, %s, %s) values(%s, %s, %s, %s);" % (
                    self.config.tbl_name,
                    self.config.primary_key,
                    self.config.status_key,
                    self.config.chat_key,
                    self.config.timestamp_key,
                    "?",
                    "?",
                    "?",
                    "?"),
                (uid, 0, chat_id, int(time())))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as ex:
            conn.close()
            if ex.args[0] == self.__class__.DUPLICATE_KEY:
                print("ERR: Duplicate UID. %s" % ex, file=stderr)
                return False
            else:
                raise

    def get_attr(self, uid, key):
        conn, cursor = self.get_conn()
        cursor.execute(
            "select %s from %s where %s = %s" % (
                key,
                self.config.tbl_name,
                self.config.primary_key,
                "?"),
            (uid,))
        res = cursor.fetchone()
        conn.close()
        if not res:
            raise self.CellNotFound()
        return res[0]

    def set_attr(self, uid, key, val):
        if not self.existed(uid):
            self.create_row(uid)
        try:
            conn, cursor = self.get_conn()
            cursor.execute(
                "update %s set %s = %s, %s = %s where %s = %s;" % (
                    self.config.tbl_name,
                    key,
                    "?",
                    self.config.timestamp_key,
                    "?",
                    self.config.primary_key,
                    "?"),
                (val, int(time()), uid))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as ex:
            conn.close()
            print("ERR: %s" % ex, file=stderr)
            return False

    def get_status(self, uid):
        try:
            return self.get_attr(uid, self.config.status_key)
        except self.CellNotFound:
            return self.__class__.ROW_NOT_FOUND_STAT

    def set_status(self, uid, status):
        return self.set_attr(uid, self.config.status_key, status)

    def export(self, addr):
        print("exporting as XLSX to %s..." % addr, file=stderr)
        wb = Workbook()
        ws = wb.active
        conn, cursor = self.get_conn()
        cursor.execute(
            "select %s from %s where %s = %s;" % (
                ", ".join(self.report_keys.keys()),
                self.config.tbl_name, self.config.status_key, "?"),
            (len(self.report_keys),))
        sheet = cursor.fetchall()
        ws.append(list(self.report_keys.values()))
        for row in sheet:
            ws.append(row)
        conn.close()
        wb.save(addr)
