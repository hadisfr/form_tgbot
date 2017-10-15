#!/usr/bin/env python3

import json
import getpass
from sys import stderr

import telebot

from dict_wrapper import DictWrapper
from db_hndlr import DBHndlr
from input_hndlr import InputHndlr

CONFIG_FILE_ADDR = "config.json"


def main():
    with open(CONFIG_FILE_ADDR) as f:
        config = DictWrapper(json.load(f))
    config.db.passwd = getpass.getpass("DB passwd for %s@%s:" % (config.db.usrname, config.db.host))
    with open(config.cols.file_addr) as f:
        cols = json.load(f)

    db_hndlr = DBHndlr(config.db, config.cols.keys, cols)
    bot = telebot.TeleBot(config.tgbot.token)
    input_hndlr = InputHndlr(bot, db_hndlr, config.cols.keys, cols, config.tgbot.msg)
    # bot.message_handler(commands=["start"])(lambda msg: db_hndlr.create_row(msg.from_user.id))
    bot.message_handler(content_types=["text"])(input_hndlr.msg_handlr)
    bot.message_handler()(lambda msg: bot.send_message(msg.chat_id, config.tgbot.msg.e400))
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
