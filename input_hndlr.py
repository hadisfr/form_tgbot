#!/usr/bin/env python3

import re

import telebot

from dict_wrapper import DictWrapper
from db_hndlr import DBHndlr


class InputHndlr:
    """form input handler"""
    def __init__(self, tg_bot, db_hndlr, form_keys, cols, msg):
        self.tg_bot = tg_bot
        self.db_hndlr = db_hndlr
        self.form_keys = form_keys
        self.cols = cols
        self.msg = msg

    def is_valid_msg(self, msg, index):
        if self.cols[index][self.form_keys.choices]:
            return msg in self.cols[index][self.form_keys.choices]
        else:
            return re.match(pattern=self.cols[index][self.form_keys.mask], string=msg)

    def get_reply_markup(self, index):
        if self.cols[index][self.form_keys.choices]:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for i in self.cols[index][self.form_keys.choices]:
                markup.add(telebot.types.KeyboardButton(i))
            return markup
        else:
            return telebot.types.ReplyKeyboardRemove()

    def get_report(self, uid):
        res = ""
        for col in self.cols:
            res += "%s %s:\t%s\n" % (
                self.msg.list_sign,
                col[self.form_keys.report_key],
                self.db_hndlr.get_attr(uid, col[self.form_keys.db_key]))
        return res

    def msg_handlr(self, msg):
        usr_id = msg.from_user.id
        chat_id = msg.chat.id
        text = msg.text
        status = self.db_hndlr.get_status(usr_id)
        self.tg_bot.send_message(chat_id, "%d\n%s\n%r" % (status, text, text == "/start"))

        if text == "/start":
            if not self.db_hndlr.existed(usr_id):
                self.db_hndlr.create_row(usr_id)
            status = 0
            self.db_hndlr.set_status(usr_id, status)
        elif status >= len(self.cols):
            pass
        elif (
                self.is_valid_msg(msg=text, index=status)
                and self.db_hndlr.set_attr(usr_id, self.cols[status][self.form_keys.db_key], text)):
            status += 1
            self.db_hndlr.set_status(usr_id, status)
        else:
            self.tg_bot.send_message(chat_id, self.msg.e422)

        if status < len(self.cols):
            self.tg_bot.send_message(
                chat_id,
                self.cols[status][self.form_keys.msg],
                reply_markup=self.get_reply_markup(status))
        else:
            self.tg_bot.send_message(chat_id, self.msg.done + self.get_report(usr_id))
