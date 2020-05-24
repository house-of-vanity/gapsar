from rutracker import Torrent
from datetime import datetime
from database import DataBase
from telegram import *
from telegram.ext import Updater, MessageHandler, CommandHandler, filters
from urllib import parse
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def main():
    """Run bot."""

    def add(update, context):
        if 'https://rutracker.org' in update.message.text:
            try:
                tor_id = parse.parse_qs(parse.urlsplit(update.message.text).query)['t'][0]
            except KeyError:
                log.warn("URL provided doesn't contains any torrent id.")
                update.message.reply_text("URL provided doesn't contains any torrent id.")
                return
        else:
            update.message.reply_text("Send me a URL to rutracker.org topic.")
            return
        log.debug(update.message.chat)
        torrent = Torrent(tor_id, update.message.chat)
        reg_time = datetime.utcfromtimestamp(int(torrent.meta['reg_time'])
                ).strftime('%b-%d')
        msg = f"""{torrent.meta['topic_title']}
<b>Size:</b> {sizeof_fmt(torrent.meta['size'])}
<b>Hash: </b> {torrent.meta['info_hash']}
<b>Updated: </b>{reg_time}"""
        log.info(msg)
        update.message.reply_text(msg, parse_mode='HTML')


    def hello(update, context):
        update.message.reply_text(
            'Hello {}'.format(update.message.from_user.first_name))


    updater = Updater("539189256:AAHqrL6nTmv5g0mGoPQownO0vrNRvhPFq7I", use_context=True)

    updater.dispatcher.add_handler(MessageHandler(filters.Filters.text, add))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
