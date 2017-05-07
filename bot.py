from functools import wraps
from io import BytesIO
import logging
import requests

import telebot
from wand.image import Image
from wand.exceptions import WandException
from mongoengine import connect

from models import Session, MemeTemplate
import messages
import config


bot = telebot.TeleBot(config.API_TOKEN)

def with_session(state=None):
    def decorator(handler):
        @wraps(handler)
        def wrapper(message):
            query = Session.objects(chat_id=message.chat.id)
            if query.count() == 0:
                return send_welcome(message)
            session = query.get()
            if state is not None and session.state != state:
                print('id =', session.chat_id)
                print('expected', state)
                print('but got', session.state)
                return unexpected_message(state)
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
    bot.send_message(message.chat.id, messages.HELLO)

def is_invited(message):
    return message.content_type == 'new_chat_member' and \
            message.new_chat_member.username == 'MakeMemeBot'

@bot.message_handler(func=is_invited, content_types=None)
@bot.message_handler(commands=['create'])
@with_session()#(state=Session.START_STATE)
def start_creation(session, message):
    session.state = Session.CHOOSING_STATE
    session.save()

    bot.reply_to(message, messages.CHOOSE_TEMPLATE,
                 reply_markup=MemeTemplate.make_markup())

@bot.message_handler(func=state_checker(Session.CHOOSING_STATE))
@with_session(Session.CHOOSING_STATE)
def choose_template(session, message):
    query = MemeTemplate.objects(name=message.text)
    if query.count() == 0:
        bot.reply_to(message, messages.INCORRECT_TEMPLATE)
    else:
        session.edit_template(query.get())
        session.save()
        bot.reply_to(message, 'You can have fun now!')
        send_image(message, session.meme.make_preview())

@bot.message_handler(commands=['set'])
@with_session(Session.EDITING_STATE)
def set_caption(session, message):
    argv = message.text.split(' ', 2)
    if len(argv) < 2:
        return bot.reply_to(message, messages.SET_USAGE)
    
    n = int(argv[1])
    text = argv[2]
    session.meme.captions[n].text = text
    session.save()
    send_image(message, session.meme.make_preview())

@bot.message_handler(commands=['make'])
@with_session(Session.EDITING_STATE)
def send_welcome(session, message):
    send_image(message, session.meme.make_meme())

#@bot.message_handler(content_types=['photo'])
@with_session(Session.SENDING_PHOTO_STATE)
def resend(session, message):
    photo_info = message.photo[-1]
    if photo_info.file_size > config.MAX_FILE_SIZE:
        return bot.reply_to(message, messages.LARGE_PHOTO)

    path = bot.get_file(photo_info.file_id).file_path
    base_url = 'https://api.telegram.org/file/bot{}/{}'
    response = requests.get(base_url.format(config.API_TOKEN, path))
    if response.status_code != 200:
        return bot.reply_to(message, messages.CANT_LOAD_PHOTO)

    blob = response.content
    try:
        Image(blob=blob).close()
    except WandException:
        bot.reply_to(message, messages.CANT_OPEN_PHOTO)
        return

    session.set_editing_custom(blob)

@bot.message_handler()
def unexpected_message(message):
    session = Session.get_session(message)
    bot.reply_to(message, messages.EXPECTED_BEHAVIOUR[session.state])

import logging

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
connect('makememebot')

if __name__ == '__main__':
    bot.polling()
