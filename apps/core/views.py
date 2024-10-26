import json
import os

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import telegram
from apps.core.telegram_bot import bot


@csrf_exempt
def webhook(request):
    print('asdfasdf')
    print(request.headers['X-Telegram-Bot-Api-Secret-Token'])
    print(os.getenv('SECRET_TOKEN'))
    if request.headers['X-Telegram-Bot-Api-Secret-Token'] == os.getenv('SECRET_TOKEN'):
        body = json.loads(request.body)
        update = telegram.Update.de_json(body, bot.bot)
        bot.dispatcher.process_update(update)
        return HttpResponse(status=200)
    return HttpResponse(status=403)
