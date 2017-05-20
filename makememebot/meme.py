from collections import namedtuple

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, \
                        IntField, StringField, ListField, BinaryField
from wand.image import Image
from wand.font import Font
from wand.color import Color
from wand.drawing import Drawing
from wand.api import library

import config


FontConfig = namedtuple('FontConfig', ['path', 'size',
                                       'color', 'outline_color'])


class Caption(EmbeddedDocument):
    left = IntField(required=True)
    top = IntField(required=True)
    width = IntField(required=True)
    height = IntField(required=True)
    text = StringField()


class Meme(EmbeddedDocument):
    image = BinaryField(max_bytes=config.MAX_FILE_SIZE, required=True)
    captions = ListField(EmbeddedDocumentField(Caption), required=True)

    def make_meme(self, font_config):
        img = Image(blob=self.image)

        for caption in self.captions:
            if caption.text:
                self._draw_caption(img, caption, font_config)

        return img

    def make_preview(self, font_config):
        img = self._make_meme(font_config)

        for i, caption in enumerate(self.captions):
            draw = Drawing()
            draw.font = config.CAPTION_NUMBER_FONT
            draw.fill_color = Color('black')
            draw.font_size=20
            draw.text(caption.left + 2, caption.top + caption.height - 2,
                      str(i + 1))
            draw.fill_opacity = 0.5
            draw.rectangle(left=caption.left, top=caption.top,
                           width=caption.width, height=caption.height)
            draw.draw(img)

        return img

    def _draw_caption(self, img, caption, font_config):
        with Image() as textboard:
            library.MagickSetOption(textboard.wand, b'stroke',
                                    font_config.outline_color.encode('utf-8'))
            library.MagickSetOption(textboard.wand, b'strokewidth', b'1.5')
            library.MagickSetSize(textboard.wand, caption.width, caption.height)
            textboard.font = Font(font_config.path, font_config.size,
                                  Color(font_config.color))
            textboard.gravity = 'center'
            with Color('transparent') as background_color:
                library.MagickSetBackgroundColor(textboard.wand,
                                                 background_color.resource)
            textboard.read(filename=b'caption:' + caption.text.encode('utf-8'))
            img.composite(textboard, caption.left, caption.top)
