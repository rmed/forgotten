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

import signal
import sys
import threading
import time


from forgotten.conf import parse_conf, get_logger

# Setup logging
logger = get_logger('launcher')

# Parse config file
parse_conf()

# Initialize database
from forgotten.dbops import DB, check_db
check_db(DB)

# Initialize bot
from forgotten.bot import bot

# Initialize worker thread
from forgotten.helper import forgotten_worker

WORKER = threading.Thread(target=forgotten_worker, daemon=True)
WORKER.start()

def sigint_handler(signal, frame):
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    print('Press Control+C to exit')

    while True:
        try:
            logger.info('Start polling')
            bot.polling(none_stop=True)

        except Exception as e:
            logger.error(e)

            logger.info('Start sleep')
            time.sleep(10)
            logger.info('Ended sleep')

            pass

        logger.info('Stop polling')
bot.stop_polling()
