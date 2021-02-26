import logging
import os
import sys
from urllib import parse

from telegram.ext import Updater, MessageHandler, CommandHandler, filters

from .notify import update_watcher
from .rutracker import Torrent
from .tools import format_topic

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

token = os.environ.get('TG_TOKEN')
if not token:
    log.error("Env var TG_TOKEN isn't set.")
    sys.exit(1)


def main():
    """Run bot."""

    def add(update, context):
        if 'https://rutracker.org' in update.message.text:
            try:
                tor_id = parse.parse_qs(parse.urlsplit(update.message.text).query)['t'][0]
            except KeyError:
                log.warning("URL provided doesn't contains any torrent id.")
                update.message.reply_text("URL provided doesn't contains any torrent id.")
                return
        else:
            update.message.reply_text("Send me a URL to rutracker.org topic.")
            return
        log.info(
            "Got /add request from user [%s] %s",
            update.message.chat['id'],
            update.message.from_user.username)
        torrent = Torrent(tor_id)
        torrent.db.save_tor(torrent.meta)
        torrent.db.save_user(update.message.chat)
        torrent.db.save_alert(update.message.chat['id'], torrent.meta['id'])
        msg = format_topic(
            torrent.meta['id'],
            torrent.meta['topic_title'],
            torrent.meta['size'],
            torrent.meta['info_hash'],
            torrent.meta['reg_time'],
            pre='You will be alerted about\n')
        update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)

    def list_alerts(update, context):
        log.info(
            "Got /list request from user [%s] %s",
            update.message.chat['id'],
            update.message.from_user.username)
        alerts = Torrent().db.get_alerts(update.message.chat['id'])
        if len(alerts) == 0:
            update.message.reply_text("You have no configured alerts.")
            return True
        msg = "<b>Configured alerts:</b>\n"
        for alert in alerts:
            msg += format_topic(
                alert['id'],
                alert['topic_title'],
                alert['size'],
                alert['info_hash'],
                alert['reg_time'],
                pre="\n")
        update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)

    def handle_client(update, context):
        u_id = update.message.chat['id']
        log.info(
            "Got /client request from user [%s] %s",
            u_id,
            update.message.from_user.username)
        try:
            addr = update.message.text.split()[1]
            log.info("Client Transmission RPC address - %s", addr)
            tr = parse.urlparse(addr)
            scheme = tr.scheme if tr.scheme else False
            hostname = tr.hostname if tr.hostname else False
            username = tr.username if tr.username else False
            password = tr.password if tr.password else False
            path = tr.path if tr.path else '/transmission/rpc'
            port = tr.port if tr.port else (80 if scheme == 'http' else 443)
            if not scheme or not hostname:
                update.message.reply_text(
                    f'Can\'t understand : <b>{update.message.text}</b>. '
                    'Send transmission RPC address like <b>http(s)://[user:pass]host[:port][/transmission/rpc]</b>',
                    parse_mode='HTML',
                    disable_web_page_preview=True)
                return
        except:
            tr_client = Torrent().db.get_client(u_id)
            log.info(tr_client)
            if tr_client:
                tr_line = f"Your client: <code>{tr_client[0]}://{tr_client[1]}:{tr_client[2]}{tr_client[5]}</code>\n" \
                          r"/delete_client"
            else:
                tr_line = False
            update.message.reply_text(
                'Gaspar can add new topics to your private Transmission server. '
                'Send transmission RPC address like \n<b>http(s)://[user:pass]host[:port][/transmission/rpc]</b>\n'
                f'{tr_line if tr_line else "You have no configured client."}',
                parse_mode='HTML',
                disable_web_page_preview=True)
            return

        if Torrent().db.add_client(u_id, scheme, hostname, port, username, password, path):
            update.message.reply_text(f'Client reachable and saved.')
        else:
            update.message.reply_text(f'Client unreachable.')

    def delete_client(update, context):
        log.info(
            "Got /delete request from user [%s] %s",
            update.message.chat['id'],
            update.message.from_user.username)
        Torrent().db.drop_client(update.message.chat['id'])
        update.message.reply_text(f'Client deleted.')

    def delete(update, context):
        log.info(
            "Got /delete request from user [%s] %s",
            update.message.chat['id'],
            update.message.from_user.username)
        tor_id = update.message.text.split('_')[1]
        try:
            Torrent().db.delete_tor(update.message.chat['id'], tor_id)
            update.message.reply_text(f'Deleted {tor_id}')
        except:
            update.message.reply_text(f'Faled to delete {tor_id}')

    updater = Updater(token, use_context=True)
    update_watcher(updater.bot)

    updater.dispatcher.add_handler(CommandHandler('list', list_alerts))
    updater.dispatcher.add_handler(CommandHandler('client', handle_client))
    updater.dispatcher.add_handler(CommandHandler('delete_client', delete_client))
    updater.dispatcher.add_handler(MessageHandler(filters.Filters.regex(r'/delete_'), delete))
    updater.dispatcher.add_handler(MessageHandler(filters.Filters.text, add))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    log = logging.getLogger('gaspar')
    main()
