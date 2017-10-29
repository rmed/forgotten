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

"""Database operations."""

import sys
import threading
from functools import wraps

import records
from forgotten.conf import SETTINGS, init_db


# Lock for operations
_LOCK = threading.Lock()

# Queries
ADD_USER = 'INSERT INTO users (tg_id, name) VALUES (:user_id, :name)'
ADD_REMINDER = (
    'INSERT INTO reminders (text, date, user_id) '
    'VALUES (:text, :date, :user_id)'
)
CREATE_TABLE_USERS = (
    'CREATE TABLE IF NOT EXISTS users ( '
    'id INTEGER PRIMARY KEY, '
    'tg_id INTEGER UNIQUE, '
    'name TEXT)'
)
CREATE_TABLE_REMINDERS = (
    'CREATE TABLE IF NOT EXISTS reminders ('
    'id INTEGER PRIMARY KEY, '
    'text TEXT, '
    'date TEXT, '
    'user_id INTEGER, '
    'FOREIGN KEY (user_id) REFERENCES users (tg_id) ON DELETE CASCADE)'
)
ENABLE_FK = 'PRAGMA foreign_keys = ON'
QUERY_TG_IDS = 'SELECT tg_id FROM users'
QUERY_REMINDERS = (
    'SELECT * FROM reminders '
    "WHERE datetime(date) < datetime('now')"
)
QUERY_USERS = 'SELECT tg_id, name FROM users'
REMOVE_USER = 'DELETE FROM users WHERE tg_id=:user_id'
REMOVE_REMINDER = 'DELETE FROM reminders WHERE id=:reminder_id'
REMOVE_REMINDERS = 'DELETE FROM reminders WHERE id IN :reminder_ids'

# Database connector
DB = init_db(SETTINGS['db_path'])

def check_db(db):
    """Make sure that foreign key support is enabled and that tables exist.

    Args:
        db: Database connector
    """
    # Enable foreign keys
    db.query(ENABLE_FK)

    # Create tables if needed
    db.query(CREATE_TABLE_USERS)
    db.query(CREATE_TABLE_REMINDERS)


def locked(func):
    """Decorator to use a thread lock to access the database."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        with _LOCK:
            return func(*args, **kwargs)

    return decorated_function

@locked
def add_user(db, user_id, name):
    """Add a new user to the database.

    Args:
        db: Database connector
        user_id (int): Telegram user ID
        name (str): Name for the user
    """
    db.query(ADD_USER, user_id=user_id, name=name)

@locked
def get_users(db):
    """Obtain a list of all users in the database.

    Args:
        db: Database connector

    Returns:
        List of users with Telegram ID and name
    """
    return db.query(QUERY_USERS)

@locked
def remove_user(db, user_id):
    """Remove a user from the database.

    Args:
        db: Database connector
        user_id (int): Telegram user ID
    """
    db.query(REMOVE_USER, user_id=user_id)

@locked
def get_tg_ids(db):
    """Obtain a list of recognized Telegram user IDs.

    Args:
        db: Database connector

    Returns:
        Query results for later iteration
    """
    return db.query(QUERY_TG_IDS)

@locked
def add_reminder(db, text, date, user_id):
    """Store a new reminder in the database.

    Args:
        db: Database connector
        text (str): Text to remind
        date (datetime): Date in which to remind the message
        user_id (int): Telegram user ID
    """
    db.query(ADD_REMINDER, text=text, date=date, user_id=user_id)

@locked
def get_active_reminders(db):
    """Obtain reminders that are ready to be sent.

    Args:
        db: Database connector
    """
    return db.query(QUERY_REMINDERS)

@locked
def remove_reminders(db, reminder_ids):
    """Remove a series of reminders from the database.

    Args:
        reminder_ids (list[int]): List of reminder IDs
    """
    #TODO bulk delete
    # db.query(REMOVE_REMINDERS, reminder_ids=reminder_ids)

    for rid in reminder_ids:
        db.query(REMOVE_REMINDER, reminder_id=rid)
