import os 
import random
import pytz
import sys
import logging

from datetime import datetime, timedelta, UTC
from enum import Enum

from django.conf import settings
from django.core.files.base import ContentFile

from telegram.ext import CommandHandler, Updater, Filters, MessageHandler, PollHandler, CallbackQueryHandler
from telegram import  InlineKeyboardMarkup, InlineKeyboardButton
from telegram import error
from telegram.ext import ConversationHandler

from apps.user_profile.models import Profile
from .models import ProfileVideoNote, Poll, PublicVideoMessage

logger = logging.getLogger('telegram')
CHAT_ADMIN = os.getenv('CHAT_ADMIN')

GET_NICKNAME = 0
class CircleBot():
    TOKEN = settings.BOT_TOKEN
    host = settings.HOST

    def __init__(self):
        self.updater = Updater(self.TOKEN, use_context=True, base_url="https://api.telegram.org/bot")
        self.dispatcher = self.updater.dispatcher
        self.bot = self.dispatcher.bot
        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.video_note, self.save_video))
        self.dispatcher.add_handler(PollHandler(self.receive_poll_answer))
        self.dispatcher.add_handler(CallbackQueryHandler(self.send_all_answer, pattern=f"^.*b_id=send_all*$"))
        self.dispatcher.add_handler(CallbackQueryHandler(self.send_video_public, pattern=f"^.*b_id={VideoMarkupButtons.SENT_PUBLIC.value}.*$"))
        self.dispatcher.add_handler(CallbackQueryHandler(self.delete_video, pattern=f"^.*b_id={VideoMarkupButtons.DELETE.value}.*$"))
        self.dispatcher.add_handler(CallbackQueryHandler(self.send_hug, pattern=f"^.*b_id={HugMarkup.Buttons.SEND_HUG.value}.*$"))
        self.dispatcher.add_handler(
            ConversationHandler(
                entry_points=[CommandHandler('set_nickname', self.set_nickname_ask)],
                fallbacks=[CommandHandler('cancel_nickname', self.cancel_nickname)],
                states={
                    GET_NICKNAME: [MessageHandler(Filters.text&(~Filters.command), self.set_nickname_answer)],
                },
            name='set_nickname')
        )
        self.dispatcher.add_handler(CommandHandler('remove_nickname', self.remove_nickname))
            

    def start(self, update, context):
        """Приветственное сообщение"""
        telegram_id = update.message["from_user"]["id"]
        profile = Profile().get_or_create_profile(telegram_id)
        update.message.reply_text(text='Привет! В этом боте обмениваются кружочками. Для чего? Просто, чтобы почувствовать поддержку, повеселиться или '\
                                        'рассказать о чувствах незнакомцу.'
                                        '\n\nТы можешь отправить пять кружков в сутки.'\
                                        '\nКружки видят все пользователи.'\
                                        '\nПосле того, как ты запишешь кружок - откроется меню с предпросмотром. Там выбираешь: отправить или удалить.'\
                                        '\n\nВ правилах нашего сообщества запрещается отправлять кружки оскорбительного содержания, насилие, эротический контент.'\
                                        ' Если на тебя кто-то пожалуется, и окажается, что ты нарушил правила сообщества, нам придется тебя забанить :('\
                                        '\n\nНо надеемся, что этого не произойдет! Ведь куда приятнее осущетсвлять общение на основе любви, принятия и чувства общности всех нас — человеков'\
                                        '\n\nЧтобы начать - просто отправляй кружок, как ты это делаешь обычно :)'
                                        )
        if profile.block_bot:
            profile.block_bot = False
            profile.save()

    def set_nickname_ask(self, update, context):
        """Сообщение о создании никнейма"""
        update.message.reply_text(text='Пришли мне никнейм, если хочешь подписыать свои кружки.'\
                                  'Не более 15 символов.'\
                                  '\nотменить - /cancel_nickname'
                                  )
        return GET_NICKNAME

    def set_nickname_answer(self, update, context):
        """Создание никнейма"""
        telegram_id = update.message["from_user"]["id"]
        profile = Profile().get_or_create_profile(telegram_id)
        message = update.message.text
        if len(message) > 15:
            update.message.reply_text(text='Слишком длинный никнейм. Надо не более 15 символов.')
            return GET_NICKNAME
        profile.nickname = message
        profile.save()
        update.message.reply_text(text=f'установил никнейм "{profile.nickname}"')
        return ConversationHandler.END
    
    def remove_nickname(self, update, context):
        """Удаление никнейма"""
        telegram_id = update.message["from_user"]["id"]
        profile = Profile().get_or_create_profile(telegram_id)
        profile.nickname = None
        profile.save()
        update.message.reply_text(text='удалил никнейм')
    
    def cancel_nickname(self, update, context):
        """Отмена редактирование никнейма"""
        update.message.reply_text(text=f'отменил установку имени')
        return ConversationHandler.END

    def send_hug(self, update, context):
        """Отправка обнимашек тому, кто прислал кружок"""
        query = update.callback_query
        profile_id = unpack_button_data(query.data)['profile_id']
        profile = Profile.objects.get(id=profile_id)
        query.answer()
        self.bot.send_message(text='отправил!', chat_id=query.from_user.id)
        self.bot.send_message(text='тебе прислали обнимашки', chat_id=profile.telegram_id)

    def send_video_public(self, update, context):
        """Отправка кружка всем пользователям"""
        update.callback_query.edit_message_text(text=f"пошел отправлять!")
        telegram_id = update.callback_query.from_user.id
        query = update.callback_query
        profile_from = Profile.objects.get(telegram_id=telegram_id)
        video_id = unpack_button_data(query.data)['video_id']
        video = ProfileVideoNote.objects.get(id=video_id)
        profiles = Profile.objects.all().exclude(telegram_id=profile_from.telegram_id)
        profiles = profiles.exclude(block_bot=True)
        cnt = 0
        for profile_to in profiles:
            try:
                markup = HugMarkup().get_markup(profile_from)
                caption = f"никнейм: {profile_from.nickname}" if profile_from.nickname else None
                self.bot.send_video(
                    video=video.file_id, 
                    chat_id=profile_to.telegram_id, 
                    reply_markup=markup,
                    caption=caption
                    )
                cnt += 1
                PublicVideoMessage.objects.create(
                    profile_from=profile_from, 
                    profile_to=profile_to, 
                    video=video
                    )
            except error.Unauthorized:
                profile_to.block_bot = True
                profile_to.save()
            except Exception as e:
                logger.error(e, exc_info=True)
        video.status = ProfileVideoNote.SentStatus.SENT
        video.save()
        self.bot.send_message(text=f"отправил стольким человекам: {cnt}!", chat_id=telegram_id)

    def delete_video(self, update, context):
        """Удаление кружка"""
        query = update.callback_query
        video_id = unpack_button_data(query.data)['video_id']
        video = ProfileVideoNote.objects.get(id=video_id)
        video.delete()
        query.edit_message_text(text='удалил кружок из базы!')

    def save_video(self, update, context, save_file=False):
        """Запись кружка для отправки всем пользователям"""
        telegram_id = update.message["from_user"]["id"]
        profile = Profile().get_or_create_profile(telegram_id)
        file_id = update.message.video_note.file_id
        video_note = self.bot.get_file(file_id)
        if profile.profile_video_notes.filter(status=ProfileVideoNote.SentStatus.WAITING).exists():
            old_video = profile.profile_video_notes.get(status=ProfileVideoNote.SentStatus.WAITING)
            update.message.reply_text('у тебя есть не разобраный кружок, отправь или удали его!')
            return Video(self.bot).send_preview(profile, old_video)
        if VideoLimit().is_exceeded(profile):
            next_time = VideoLimit().get_next_time_to_send(profile)
            return update.message.reply_text(text=f'У тебя закончились свободные кружки в эти сутки. \n\nВремя обновления лимита: {next_time}')
        if save_file:
            video_note_file = ContentFile(video_note.download_as_bytearray(), name=os.path.basename(video_note.file_path))
        else:
            video_note_file = None
        video_note = ProfileVideoNote.objects.create(profile=profile, file_id=file_id, file=video_note_file)
        Video(self.bot).send_preview(profile, video_note)


    def send_all(self, update, context):
        "Подготовка к отправке сообщения от администратора всем пользователям"
        telegram_id = update.message["from_user"]["id"]
        message = update.message.text.split('отправить всем')[1]
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('отправить', callback_data='b_id=send_all')]])
        if telegram_id == CHAT_ADMIN:
            update.message.reply_text(text=message, reply_markup=markup)

    def send_all_answer(self, update, context):
        "Отправка сообщения от администратора всем пользователям"
        message = update.callback_query.message.text
        cnt = 0
        logger.info('start sending messages')
        for profile in Profile.objects.all():
            try:
                self.bot.send_message(text=message, chat_id=profile.telegram_id)
                cnt += 1
                logger.info(f'send {cnt} messages')
            except Exception as e:
                logger.error(e, exc_info=True)
        logger.info(f'end sending,  {cnt} messages')
        update.callback_query.edit_message_text(text=f"отправил {cnt} сообщений!")

    def receive_poll_answer(self, update, context) -> None:
        poll_bot = update.poll
        poll = Poll.objects.get(telegram_id=poll_bot.id)
        for option_bot in poll_bot.options:
            option = poll.poll_options.get(text=option_bot.text)
            option.count = option_bot.total_vouter_count
            option.save()

class Video():
    def __init__(self, bot) -> None:
        self.bot = bot
    
    def send_preview(self, profile, video):
        caption = f"никнейм: {profile.nickname}" if profile.nickname else None
        self.bot.send_video(chat_id=profile.telegram_id, video=video.file_id, caption=caption)
        text, reply_markup = VideoMarkup(video).get_markup()
        self.bot.send_message(text=text, reply_markup=reply_markup, chat_id=profile.telegram_id)

def unpack_button_data(data):
    data = dict([element.split('=') for element in data.split(":")])
    for key, value in data.items():
        data[key] = int(value) if value.isnumeric() else value
    return data


class HugMarkup():
    class Buttons(Enum):
        SEND_HUG = 'send_hug'

    def get_markup(self, profile):
         button = [InlineKeyboardButton(
                    text='обнимашки',
                    callback_data=f'profile_id={profile.id}:b_id={HugMarkup.Buttons.SEND_HUG.value}')]
         return InlineKeyboardMarkup([button])


class VideoMarkupButtons(Enum):
    SENT_PUBLIC = 'public'
    DELETE = 'delete'


class VideoMarkup():
    def __init__(self, video) -> None:
        self.video = video

    def get_markup(self):
        buttons = [
            [InlineKeyboardButton(
                'отправить всем', 
                callback_data=f'b_id={VideoMarkupButtons.SENT_PUBLIC.value}:video_id={self.video.id}'
                )
            ],
            [InlineKeyboardButton(
                'удалить', 
                callback_data=f'b_id={VideoMarkupButtons.DELETE.value}:video_id={self.video.id}'
                )
            ]
        ]
        return 'что сделать с кружком?', InlineKeyboardMarkup(buttons)


class VideoLimit():
    """Калсс для проверки лимита кружков пользователя"""
    ONE_DAY_VIDEO_LIMIT = 5
    HOUR_FROM = 0

    def is_exceeded(self, profile):
        limit_from_datetime = datetime.now(UTC).replace(hour=self.HOUR_FROM, minute=0)
        videos = profile.profile_video_notes.filter(created_at__gt=limit_from_datetime)
        if len(videos) >= self.ONE_DAY_VIDEO_LIMIT and profile.has_limit:
            return True
        return False
    
    def get_next_time_to_send(self, profile):
        next_date = (datetime.now(UTC)+timedelta(days=1)).replace(hour=self.HOUR_FROM, minute=0)
        return next_date.astimezone(pytz.timezone('Europe/Moscow')).strftime(format="%m/%d/%Y, %H:%M (МСК)")

class PollSender():
    """Калсс для организации голосований в боте"""
    def __init__(self, bot) -> None:
        self.bot = bot

    def start_poll(self, poll):
        if poll.sent:
            return 
        options = list(poll.poll_options.all().values_list('text', flat=True))
        # сначала отправка голосования админу, чтобы можо было переслать сообещение
        res = self.bot.bot.send_poll(question=poll.question, options=options, chat_id=CHAT_ADMIN)
        count = 0
        # рассылка сообщения-голосования всем
        for profile in Profile.objects.all():
            try:
                self.bot.bot.forward_message(from_chat_id=CHAT_ADMIN, message_id=res.message_id, chat_id=profile.telegram_id)
                count += 1
            except Exception:
                pass
        poll_id = res.poll.id
        poll.telegram_id = poll_id
        poll.sent = True
        poll.save()
        self.bot.bot.send_message(text=f'переслал голосование {count}', chat_id=CHAT_ADMIN)



bot = CircleBot()