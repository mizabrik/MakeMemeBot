from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, \
                        IntField, StringField, ListField, BinaryField
from wand.image import Image
from wand.font import Font
from wand.color import Color
from wand.drawing import Drawing

class Caption(EmbeddedDocument):
    left = IntField(required=True)
    top = IntField(required=True)
    width = IntField(required=True)
    height = IntField(required=True)
    text = StringField()


def draw_caption(img, caption):
    font_path = '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'
    font = Font(font_path, color=Color('black'))

    stroke_coordinates = [
        (caption.top - 1, caption.left + 1),
        (caption.top - 1, caption.left - 1),
        (caption.top + 1, caption.left - 1),
        (caption.top + 1, caption.left + 1),
    ]

    # Sloooow
    #for top, left in stroke_coordinates:
    #    img.caption(caption.text, left, top,
    #                caption.width, caption.height, font, 'center')

    #font = Font(font_path, color=Color('white'))
    img.caption(caption.text, caption.left, caption.top,
                caption.width, caption.height, font, 'center')

class Meme(EmbeddedDocument):
    image = BinaryField(max_bytes=2**22, required=True)
    captions = ListField(EmbeddedDocumentField(Caption), required=True)

    def make_meme(self):
        with self._make_meme() as img:
            return img.make_blob()

    def make_preview(self):
        with self._make_preview() as img:
            return img.make_blob()

    def _make_meme(self):
        img = Image(blob=self.image)

        for caption in self.captions:
            if caption.text:
                draw_caption(img, caption)

        return img

    def _make_preview(self):
        img = self._make_meme()

        for i, caption in enumerate(self.captions):
            draw = Drawing()
            draw.font = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
            draw.stroke_color = Color('black')
            draw.stroke_width = 1
            draw.fill_color = Color('white')
            draw.font_size=20
            draw.text(caption.left + 2, caption.top + caption.height - 2,
                      str(i + 1))
            draw.fill_opacity = 0.5
            draw.rectangle(left=caption.left, top=caption.top,
                           width=caption.width, height=caption.height)
            draw.draw(img)

        return img
