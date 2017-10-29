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

"""Telegram bot implementation."""

import datetime
import logging
import os
import time

import telebot
from forgotten.conf import SETTINGS
from forgotten.dbops import DB
from forgotten import dbops

telebot.logger.setLevel(logging.INFO)

# Initialize bot
bot = telebot.TeleBot(
    SETTINGS['token'],
    threaded=True,
    skip_pending=True
)

from forgotten.helper import needs_owner, needs_user, is_cancel_cmd

# Owner commands

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """Initialize the bot and show help about commands."""
    response = (
        'Forgotten: reminders on demand\n\n'
        'Commands:\n\n'
        '/adduser <tg_id> <name> (admin command)\n'
        '/listusers (admin command)\n'
        '/rmuser <tg_id> (admin command)\n'
        '/me -> find Telegram ID\n'
        '/remember -> ask for date and text to remember\n'
        '/remember <datetime> -> ask for text to remember'
    )

    bot.reply_to(message, response)

@bot.message_handler(commands=['me'])
def me(message):
    """Return Telegram ID."""
    bot.reply_to(message, message.chat.id)

@bot.message_handler(commands=['adduser'])
@needs_owner
def handle_adduser(message):
    """Add a user to the database.

    Owner command. Syntax:

        /adduser <telegram_id:int> <name:str>
    """
    # Get arguments
    args = telebot.util.extract_arguments(message.text).split()

    if len(args) != 2:
        bot.reply_to(message, 'Missing arguments: /adduser <id> <name>')
        return

    user_id = args[0]
    name = args[1]

    if not user_id.isdigit():
        bot.reply_to(message, 'Not a valid Telegram ID')
        return

    # Add user to database
    try:
        dbops.add_user(DB, int(user_id), name)

    except Exception as e:
        bot.reply_to(message, 'Failed to insert user: %s' % e)
        return

    bot.reply_to(message, 'New user "%s" created' % name)

@bot.message_handler(commands=['listusers'])
@needs_owner
def handle_listusers(message):
    """List users in the database.

    Owner command. Syntax:

        /listusers
    """
    to_send = ''
    for user in dbops.get_users(DB):
        to_send += '- %d: %s\n' % (user.tg_id, user.name)

    if not to_send:
        to_send = 'No users in database'

    bot.reply_to(message, to_send)

@bot.message_handler(commands=['rmuser'])
@needs_owner
def handle_rmuser(message):
    """Remove user from the database.

    Owner command. Syntax:

        /rmuser <telegram_id:int>
    """
    # Get argument
    user_id = telebot.util.extract_arguments(message.text)

    if not user_id or not user_id.isdigit():
        bot.reply_to(message, 'Missing argument: /rmuser <id>')
        return

    # Remove user from database
    try:
        dbops.remove_user(DB, int(user_id))

    except Exception as e:
        bot.reply_to(message, 'Failed to remove user: %s' % e)
        return

    bot.reply_to(message, 'User "%s" removed' % user_id)

# User commands

@bot.message_handler(commands=['remember'])
@needs_user
def handle_remember(message):
    """Create a new reminder.

    User command. Syntax:

        /remember <date:datetime>

    If date is not provided, the user will be asked for it.
    """
    # Try to obtain date
    arg = telebot.util.extract_arguments(message.text)

    if arg:
        try:
            date = datetime.datetime.strptime(arg, '%Y-%m-%d %H:%M')

        except ValueError:
            # Invalid date
            bot.reply_to(message, 'Date must be in format YYYY-MM-DD hh:mm')
            return

        # Continue with text
        reply = bot.reply_to(
            message,
            'Specify a message or send a photo to remember, or cancel with /cancel'
        )

        bot.register_next_step_handler(
            reply,
            lambda m: _remember_content(m, date)
        )

        return

    # No date provided, ask for it
    reply = bot.reply_to(
        message,
        'Specify a date for the reminder in YYYY-MM-DD hh:mm format'
    )

    bot.register_next_step_handler(reply, _remember_date)

def _remember_date(message):
    """Ask for the date in which to remember something.

    Date must be in YYYY-MM-DD hh:mm format.
    """
    if not message.text or is_cancel_cmd(message):
        return

    try:
        date = datetime.datetime.strptime(message.text, '%Y-%m-%d %H:%M')

    except ValueError:
        # Invalid date
        reply = bot.reply_to(message, 'Date must be in format YYYY-MM-DD hh:mm')
        bot.register_next_step_handler(reply, _remember_date)
        return

    # Obtained date, continue with text
    reply = bot.send_message(
        message.chat.id,
        'Specify a message or send a photo to remember, or cancel with /cancel'
    )

    bot.register_next_step_handler(reply, lambda m: _remember_content(m, date))

def _remember_content(message, date):
    """Ask for the content to remember.

    Content may be a text or photo.
    """
    if message.content_type not in ('text', 'photo'):
        reply = bot.reply_to(message, 'Content must be a text or a photo')
        bot.register_next_step_handler(
            reply,
            lambda m: _remember_content(m, date)
        )
        return

    # Text
    if message.text:
        if is_cancel_cmd(message):
            return

        # Store reminder
        try:
            dbops.add_reminder(DB, message.text, date, message.chat.id)

        except Exception as e:
            bot.reply_to(message, 'Failed to store reminder: %s' % e)
            return

    # Photo
    if message.photo:
        # Get photo with original size
        photosize = message.photo[-1]
        file_info = bot.get_file(photosize.file_id)
        downloaded = bot.download_file(file_info.file_path)

        store_path = os.path.join(SETTINGS['media_path'], str(time.time()))

        while os.path.exists(store_path):
            store_path = os.path.join(SETTINGS['media_path'], str(time.time()))

        with open(store_path, 'wb') as new_file:
            try:
                new_file.write(downloaded)

            except Exception as e:
                bot.reply_to(message, 'Failed to store photo: %s' % e)
                return

        # Store reminder
        try:
            dbops.add_reminder(
                DB,
                '_photo:%s' % store_path,
                date,
                message.chat.id
            )

        except Exception as e:
            bot.reply_to(message, 'Failed to store reminder: %s' % e)
            os.unlink(store_path)
            return

    bot.send_message(message.chat.id, 'Reminder stored!')
