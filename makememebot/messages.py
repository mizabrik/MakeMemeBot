from makememebot.models import Session
from makememebot.utils import human_size
import config

HELLO = 'Hello! Use command /create to create meme.'
NEW_ADVICE = 'Send me the image, you want to use as a background'
LARGE_PHOTO = 'This photo is too large. Only files under 3MiB are supported'
CANT_LOAD_PHOTO = 'I am not able to get the photo :( Please, try again!'
CHOOSE_TEMPLATE = 'Okay. Choose one of provided templates now.'
SET_USAGE = 'To set caption N to TEXT, send /set N TEXT'
INCORRECT_TEMPLATE = 'No such template :( Choose one from keyboard, pls.'
SEND_CUSTOM = 'Now send your photo, not larger than {}'.format(
    human_size(config.MAX_FILE_SIZE))
SETTINGS = 'Font: {}\nFont size: {}\nText color: {}\nOutline color: {}'

SETfONT_USAGE = '/setfont FONT, where FONT is one of dejavu, opensans'

HELP = "I will help you with making memes.\n" \
       "/create will lead you to choosing a template, " \
       "after that you'll be able to set captions with /set command. " \
       "Finally, you can get the meme with /make command.\n" \
       "You can always go to the beginning with help of /start command."

EXPECTED_BEHAVIOUR = {
    Session.START_STATE: 'Send /create to create meme from template',
    Session.EDITING_STATE: 'Use /set command to edit captions and /make to'
                           'get the meme. You can quit with /start.',
    Session.SENDING_PHOTO_STATE: 'Please, send a photo not larger than 3MiB.'
}
