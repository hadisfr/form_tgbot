#!/usr/bin/env python3

import json
import getpass
from sys import stderr

from dict_wrapper import DictWrapper
from db_hndlr import DBHndlr

CONFIG_FILE_ADDR = "config.json"


def main():
    with open(CONFIG_FILE_ADDR) as f:
        config = DictWrapper(json.load(f))
    config.db.passwd = getpass.getpass("DB passwd for %s@%s:" % (config.db.usrname, config.db.host))
    with open(config.cols.file_addr) as f:
        cols = json.load(f)

    db_hndlr = DBHndlr(config.db, config.cols.keys, cols)


if __name__ == '__main__':
    main()
