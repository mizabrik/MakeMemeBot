from models import Session

HELLO = 'Hello! Use command /create to create meme.'
NEW_ADVICE = 'Send me the image, you want to use as a background'
LARGE_PHOTO = 'This photo is too large. Only files under 3MiB are supported'
CANT_LOAD_PHOTO = 'I am not able to get the photo :( Please, try again!'
CHOOSE_TEMPLATE = 'Okay. Choose one of provided templates now.'
SET_USAGE = 'To set caption N to TEXT, send /set N TEXT'

EXPECTED_BEHAVIOUR = {
    Session.EDITING_STATE: 'Use /set command to edit captions and /make to'
                           'get the meme. You can quit with /start.',
    Session.SENDING_PHOTO_STATE: 'Please, send a photo not larger than 3MiB.'
}
