from django.core.management.base import BaseCommand
from django.conf import settings
import os
import uuid

from telegram import Bot
from telegram.ext import Dispatcher

from apps.core.telegram_bot import bot


class Command(BaseCommand):
    help = """Привязка вебхуку боту"""

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--webhook',
            action='store_true',
            help='Привязать вебхук',
        )

    def handle(self, *args, **options):
        if options['webhook']:
            bot.bot = Bot(settings.BOT_TOKEN, base_url="https://api.telegram.org/bot")
            self.dispatcher = Dispatcher(bot.bot, None, use_context=True)
            print(os.getenv('HOST')+'/webhook')
            bot.bot.set_webhook(url=os.getenv('HOST')+'/webhook', api_kwargs={'secret_token': os.getenv('SECRET_TOKEN')})
        else:
            bot.updater.start_polling()