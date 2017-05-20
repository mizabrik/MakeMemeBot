from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, \
                        LongField, StringField, ListField, BinaryField
from wand.image import Image
from wand.font import Font
from wand.color import Color
from wand.drawing import Drawing
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from makememebot.meme import Meme, Caption, FontConfig
from config import FONTS, DEFAULT_FONT

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
    font_name = StringField(required=True, default=DEFAULT_FONT)
    font_size = LongField(required=True, default=30, min_value=0)
    font_color = StringField(required=True, default='white')
    outline_color = StringField(required=True, default='black')

    @classmethod
    def get_session(cls, message):
        return cls.objects(chat_id=message.chat.id).get()

    def set_editing_custom(self, image):
        w, h = image.width, image.height
        captions = [
            Caption(round(0.05 * w), round(0.02 * h), 
                    round(0.9 * w), round(0.15 * h)),
            Caption(round(0.05 * w), round(0.83 * h), 
                    round(0.9 * w), round(0.15 * h)),
        ]
        self.meme = Meme(image.make_blob(), captions)
        self.state = Session.EDITING_STATE

    def edit_template(self, template):
        self.meme = template.meme
        self.state = Session.EDITING_STATE

    def make_meme(self):
        with self.meme.make_meme(self.get_font_config()) as img:
            return img.make_blob()

    def make_preview(self):
        with self.meme.make_preview(self.get_font_config()) as img:
            return img.make_blob()

    def get_font_config(self):
        return FontConfig(FONTS[self.font_name], self.font_size,
                          self.font_color, self.outline_color)
