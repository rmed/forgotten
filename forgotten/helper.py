# -*- coding: utf-8 -*-
#
# forgotten
# https://github.com/rmed/forgotten
#
# The MIT License (MIT)
#
# Copyright (c) 2017 Rafael Medina García <rafamedgar@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Helper functions."""

import os
import time
from functools import wraps

import telebot
from forgotten import dbops
from forgotten.bot import bot
from forgotten.conf import SETTINGS, get_logger
from forgotten.dbops import DB


logger = get_logger('helper')


def forgotten_worker():
    """Thread worker that continuously checks for active reminders."""
    wait_time = SETTINGS['wait_time']
    logger.info('starting worker thread with a waiting time of %d' % wait_time)

    while True:
        reminders = dbops.get_active_reminders(DB)

        # Send reminders that are ready
        to_delete = []

        for reminder in reminders:
            to_delete.append(reminder.id)

            if reminder.text.startswith('_photo:'):
                # Must send photo
                file_path = reminder.text.replace('_photo:', '')

                if not os.path.exists(file_path):
                    bot.send_message(reminder.user_id, 'Cannot find photo')
                    return

                # Send file
                with open(file_path, 'rb') as photo:
                    bot.send_photo(reminder.user_id, photo)

                # Remove file
                os.unlink(file_path)

                continue

            # Send text
            bot.send_message(reminder.user_id, reminder.text)

        # Remove old reminders
        if to_delete:
            dbops.remove_reminders(DB, to_delete)

        time.sleep(wait_time)

def needs_owner(func):
    """Decorator to require the owner for the given function."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if args[0].chat.id != SETTINGS['owner']:
            bot.reply_to(args[0], 'Sorry, you are not the owner of this bot')
            return

        return func(*args, **kwargs)

    return decorated_function

def needs_user(func):
    """Decorator to require a user for the given function."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        for row in dbops.get_tg_ids(DB):
            if row.tg_id == args[0].chat.id:
                return func(*args, **kwargs)

        bot.reply_to(args[0], "Sorry, I don't recognize you. Contact the admin")

    return decorated_function

def is_cancel_cmd(message):
    """Check whether the message is a '/cancel' command.

    Args:
        message: Received Telegram message.

    Returns:
        True if it is a '/cancel' message, otherwise False.
    """
    cmd = telebot.util.extract_command(message.text)
    if cmd and cmd == 'cancel':
        bot.reply_to(message, 'Operation cancelled')

        return True

    return False
