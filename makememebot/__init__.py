from functools import wraps
from io import BytesIO
import logging
import requests

import telebot
from telebot.types import ReplyKeyboardRemove
from wand.image import Image
from wand.color import Color
from wand.exceptions import WandException
from mongoengine import connect

from makememebot.models import Session, MemeTemplate
import makememebot.messages as msgs
import config

__all__ = ['bot', 'run_polling']

bot = telebot.TeleBot(config.API_TOKEN)
connect('makememebot')

def with_session(state=None):
    def decorator(handler):
        @wraps(handler)
        def wrapper(message):
            query = Session.objects(chat_id=message.chat.id)
            if query.count() == 0:
                return send_welcome(message)
            session = query.get()
            if state is not None and session.state != state:
                return unexpected_message(message)
            return handler(session, message)

        return wrapper

    return decorator

def state_checker(state):
    def checker(message):
        query = Session.objects(chat_id=message.chat.id)
        return query.count() > 0 and query.get().state == state
    return checker

def send_image(message, img):
    stream = BytesIO(img)
    bot.send_photo(message.chat.id, stream)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, msgs.HELP)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    query = Session.objects(chat_id=message.chat.id)
    if query.count() == 0:
        session = Session(message.chat.id)
    else:
        session = query.get()
        session.meme = None
    session.state = Session.START_STATE
    session.save()
    bot.send_message(message.chat.id, msgs.HELLO)

def is_invited(message):
    return message.content_type == 'new_chat_member' and \
            message.new_chat_member.username == 'MakeMemeBot'

@bot.message_handler(func=is_invited, content_types=None)
@bot.message_handler(commands=['create'])
@with_session()#(state=Session.START_STATE)
def start_creation(session, message):
    session.state = Session.CHOOSING_STATE
    session.save()

    bot.reply_to(message, msgs.CHOOSE_TEMPLATE,
                 reply_markup=MemeTemplate.make_markup())

@bot.message_handler(func=state_checker(Session.CHOOSING_STATE))
@with_session(Session.CHOOSING_STATE)
def choose_template(session, message):
    query = MemeTemplate.objects(name=message.text)
    if query.count() == 0:
        bot.reply_to(message, msgs.INCORRECT_TEMPLATE)
    else:
        session.edit_template(query.get())
        session.save()
        bot.reply_to(message, 'You can have fun now!',
                     reply_markup=ReplyKeyboardRemove(selective=True))
        send_image(message, session.meme.make_preview())

@bot.message_handler(commands=['set'])
@with_session(Session.EDITING_STATE)
def set_caption(session, message):
    argv = message.text.split(' ', 2)
    if len(argv) < 2:
        return bot.reply_to(message, msgs.SET_USAGE)
    
    try:
        n = int(argv[1]) - 1
    except ValueError:
        return bot.reply_to(message, msgs.SET_USAGE)
    text = argv[2]
    if not 0 <= n <= len(session.meme.captions):
        return bot.reply_to(message, msgs.SET_USAGE)
    session.meme.captions[n].text = text
    session.save()
    send_image(message, session.make_preview())

@bot.message_handler(commands=['make'])
@with_session(Session.EDITING_STATE)
def make_meme(session, message):
    send_image(message, session.make_meme())

@bot.message_handler(commands=['custom'])
@with_session()
def create_custom(session, message):
    session.state = Session.SENDING_PHOTO_STATE
    session.save()
    bot.reply_to(message, msgs.SEND_CUSTOM)

@bot.message_handler(content_types=['photo'])
@with_session(Session.SENDING_PHOTO_STATE)
def edit_custom(session, message):
    photo_info = message.photo[-1]
    if photo_info.file_size > config.MAX_FILE_SIZE:
        return bot.reply_to(message, msgs.LARGE_PHOTO)

    path = bot.get_file(photo_info.file_id).file_path
    base_url = 'https://api.telegram.org/file/bot{}/{}'
    response = requests.get(base_url.format(config.API_TOKEN, path))
    if response.status_code != 200:
        return bot.reply_to(message, msgs.CANT_LOAD_PHOTO)

    blob = response.content
    try:
        image = Image(blob=blob)
    except WandException:
        bot.reply_to(message, msgs.CANT_OPEN_PHOTO)
        return

    session.set_editing_custom(image)
    session.save()
    image.close()

@bot.message_handler(commands=['settings'])
@with_session()
def show_settings(session, message):
    settings = msgs.SETTINGS.format(session.font_name, session.font_size,
                                    session.font_color, session.outline_color)
    bot.reply_to(message, settings)

@bot.message_handler(commands=['setfont'])
@with_session()
def set_font_size(session, message):
    argv = message.text.split(' ', 2)
    if len(argv) != 2:
        return bot.reply_to(message, msgs.SETFONT_USAGE)
    font = argv[1]
    if font not in config.FONTS:
        return bot.reply_to(message, msgs.SETFONT_USAGE)

    session.font_name = font
    session.save()

@bot.message_handler(commands=['setfontsize'])
@with_session()
def set_font_size(session, message):
    argv = message.text.split(' ', 2)
    if len(argv) != 2:
        return bot.reply_to(message, msgs.SETFONTSIZE_USAGE)
    try:
        size = int(argv[1])
    except ValueError:
        return bot.reply_to(message, msgs.SETFONTSIZE_USAGE)
    if size <= 0:
        return bot.reply_to(message, msgs.SETFONTSIZE_USAGE)

    session.font_size = size
    session.save()

@bot.message_handler(commands=['setfontcolor'])
@with_session()
def set_font_color(session, message):
    argv = message.text.split(' ', 2)
    if len(argv) != 2:
        return bot.reply_to(message, msgs.SETFONTCOLOR_USAGE)
    color = argv[1]

    session.font_color = color
    session.save()

@bot.message_handler(commands=['setoutlinecolor'])
@with_session()
def set_outline_color(session, message):
    argv = message.text.split(' ', 2)
    if len(argv) != 2:
        return bot.reply_to(message, msgs.SETOUTLINECOLOR_USAGE)
    color = argv[1]

    session.outline_color = color
    session.save()

@bot.message_handler()
@with_session()
def unexpected_message(session, message):
    bot.reply_to(message, msgs.EXPECTED_BEHAVIOUR[session.state])

def run_polling():
    telebot.logger.setLevel(logging.DEBUG)
    bot.polling()
