from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, \
                        LongField, StringField, ListField, BinaryField
from wand.image import Image
from wand.font import Font
from wand.color import Color
from wand.drawing import Drawing
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from meme import Meme

class MemeTemplate(Document):
    name = StringField(required=True, unique=True)
    meme = EmbeddedDocumentField(Meme, required=True)

    @classmethod
    def make_markup(cls):
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
        for template in cls.objects.only('name'):
            markup.add(KeyboardButton(template.name))

        return markup

class Session(Document):
    START_STATE = "start"
    CHOOSING_STATE = "choosing"
    SENDING_PHOTO_STATE = "sending"
    EDITING_STATE = "editing"

    chat_id = LongField(required=True, unique=True)
    state = StringField(
        required=True, default=START_STATE, choices=[
            START_STATE, CHOOSING_STATE, SENDING_PHOTO_STATE, EDITING_STATE
        ]
    )
    meme = EmbeddedDocumentField(Meme)

    @classmethod
    def get_session(cls, message):
        return cls.objects(chat_id=message.chat.id).get()

    def set_editing_custom(self, blob):
        pass

    def edit_template(self, template):
        self.meme = template.meme
        self.state = Session.EDITING_STATE
