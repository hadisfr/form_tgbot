#!/usr/bin/env python3

import json
import traceback
from sys import stderr

import telebot

from dict_wrapper import DictWrapper
from db_hndlr import DBHndlr
from input_hndlr import InputHndlr

CONFIG_FILE_ADDR = "config.json"


def main():
    with open(CONFIG_FILE_ADDR) as f:
        config = DictWrapper(json.load(f))
    with open(config.cols.file_addr) as f:
        cols = json.load(f)

    while True:
        try:
            db_hndlr = DBHndlr(config.db, config.cols.keys, cols)
            bot = telebot.TeleBot(config.tgbot.token)
            bot.admins = config.tgbot.admins
            input_hndlr = InputHndlr(bot, db_hndlr, config.cols.keys, cols, config.tgbot.msg, config.report_file_addr, config.db)
            bot.message_handler(commands=["report"])(input_hndlr.send_report)
            bot.message_handler(content_types=["text"])(input_hndlr.msg_handlr)
            bot.message_handler()(lambda msg: bot.send_message(msg.chat.id, config.tgbot.msg.e400))
            bot.polling(none_stop=True)
        except Exception as ex:
            print(ex, file=stderr)
            traceback.print_exc()


if __name__ == '__main__':
    main()
