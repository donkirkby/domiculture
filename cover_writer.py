from pathlib import Path

from reportlab.graphics import renderPM, renderPDF
from reportlab.graphics.shapes import Drawing, Rect, Image, String, Group
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from space_tracer import LivePillowImage
# noinspection PyPackageRequirements
import PIL.Image
# noinspection PyPackageRequirements
import PIL.ImageDraw
from svglib.svglib import svg2rlg

from font_set import register_fonts


class Cover:
    def __init__(self):
        self.total_width = 9.06 * inch
        self.total_height = 7.125 * inch
        self.spine = 0.31 * inch
        self.margin = 0.5 * inch
        self.bleed = 0.125 * inch

    def draw(self) -> Drawing:
        register_fonts(include_courier=True)
        drawing = Drawing(self.total_width, self.total_height)
        cover_left = (self.total_width + self.spine) / 2
        cover_width = (self.total_width - self.spine) / 2
        front_only = False
        if front_only:
            with PIL.Image.open('cover/cover.jpg') as cover_raw:
                aspect = cover_width / self.total_height
                raw_height = cover_raw.height
                crop_height = raw_height
                crop_width = crop_height * aspect
                x0 = 1200
                y0 = 0
                x1 = crop_width + x0
                y1 = crop_height + y0

                cropped = cover_raw.crop((x0, y0, x1, y1))
                cropped.save('cover/cover_cropped.jpg')
            drawing.add(Image(cover_left, 0,
                              cover_width, self.total_height,
                              'cover/cover_cropped.jpg'))
        else:
            with PIL.Image.open('cover/cover.jpg') as cover_raw:
                aspect = self.total_width / self.total_height
                raw_height = cover_raw.height
                crop_height = raw_height * 0.89
                crop_width = crop_height * aspect
                x0 = 0
                y0 = 200
                x1 = round(crop_width + x0)
                y1 = round(crop_height + y0)

                cropped = cover_raw.crop((x0, y0, x1, y1))
                cropped.save('cover/cover_cropped.jpg')
            drawing.add(Image(0, 0,
                              self.total_width, self.total_height,
                              'cover/cover_cropped.jpg'))
        # self.add_border(drawing)
        mid_cover = self.total_width*3/4 + self.spine/4 - self.bleed/2
        drawing.add(String(mid_cover, self.total_height * 0.59,
                           'Donimoes',
                           fontName='Fredoka',
                           fontSize=self.total_height/11,
                           fillColor=Color(0.85, 0.85, 0.85),
                           textAnchor='middle'))
        medium_font_size = self.total_height / 30
        drawing.add(String(mid_cover, self.total_height * 0.55,
                           'New Games and Puzzles',
                           fontName='Raleway-Italic',
                           fontSize=medium_font_size,
                           fillColor=Color(0.85, 0.85, 0.85),
                           textAnchor='middle'))
        drawing.add(String(mid_cover, self.margin + self.bleed,
                           'Don Kirkby',
                           fontName='Raleway',
                           fontSize=medium_font_size,
                           fillColor=Color(0.85, 0.85, 0.85),
                           textAnchor='middle'))

        small_font_size = self.total_height / 50
        lines = ["A dozen games and puzzles that will take you",
                 "beyond a chain of dominoes with matching",
                 "numbers. You'll find my new games and puzzles,",
                 "as well as my favourites from other designers."]
        x = self.margin + self.bleed
        y = self.total_height * 0.78
        self.draw_text_box(drawing, lines, x, y, small_font_size)
        lines = ["It might be the best new use of",
                 "dominoes since Sid Sackson's",
                 "The Domino Bead Game.",
                 "-- Kerry Handscomb,",
                 "    Abstract Games Magazine"]
        x = self.total_width * 0.17
        y = self.total_height * 0.56
        self.draw_text_box(drawing, lines, x, y, small_font_size)

        spine_group = Group(String(-self.margin - self.bleed, self.total_width / 2 - self.spine / 5,
                                   'Don Kirkby',
                                   fontName='Raleway',
                                   fontSize=self.total_height / 40,
                                   fillColor=Color(0.85, 0.85, 0.85),
                                   textAnchor='end'),
                            String(-self.total_height/2, self.total_width / 2 - self.spine / 5,
                                   'Donimoes',
                                   fontName='Raleway',
                                   fontSize=self.total_height / 40,
                                   fillColor=Color(0.85, 0.85, 0.85),
                                   textAnchor='middle')
                            )
        spine_group.rotate(-90)
        drawing.add(spine_group)

        isbn = svg2rlg('cover/isbn.svg')
        isbn_frame_width = isbn.width*1.2
        isbn_frame_height = isbn.height*1.4
        drawing.add(Rect((self.total_width-self.spine)/2 -
                         self.margin-isbn_frame_width,
                         self.bleed+self.margin,
                         isbn_frame_width,
                         isbn_frame_height,
                         fillColor=Color(1, 1, 1),
                         strokeColor=None))
        isbn.translate((self.total_width-self.spine)/2-self.margin -
                       (isbn.width+isbn_frame_width)/2,
                       self.bleed+self.margin+(isbn_frame_height-isbn.height)/2)
        drawing.add(isbn)

        return drawing

    def draw_text_box(self, drawing, lines, x, y, font_size):
        cover = PIL.Image.open('cover/cover_cropped.jpg')
        scale = cover.width / self.total_width

        width = max(pdfmetrics.stringWidth(line, 'Raleway', font_size)
                    for line in lines)
        height = (len(lines)+0.5)*font_size
        padded_width = round((width+2*font_size)*scale)
        padded_height = round((height+2*font_size)*scale)
        image = PIL.Image.new('RGB', (padded_width, padded_height))
        paint = PIL.ImageDraw.Draw(image)
        paint.rectangle((0, 0, padded_width, padded_height), 'black')
        steps = 32
        for step in range(steps):
            padding = round(step * font_size / steps * scale)
            grey = round(step * 50 / steps)
            grey_rgb = f'#{grey:02x}{grey:02x}{grey:02x}'
            paint.rounded_rectangle((padding,
                                     padding,
                                     padded_width-2*padding,
                                     padded_height-2*padding),
                                    font_size*scale,
                                    fill=grey_rgb)
        mask = image.convert('L')

        paint.rectangle((0, 0, padded_width, padded_height), fill='brown')
        image.putalpha(mask)
        cover.paste(image,
                    (round((x-font_size)*scale),
                     round(cover.height-(y+font_size*2)*scale)),
                    image)
        cover.save('cover/cover_cropped.jpg')
        for i, line in enumerate(lines):
            drawing.add(String(x,
                               y - i * font_size,
                               line,
                               fontName='Raleway',
                               fontSize=font_size,
                               fillColor=Color(0.85, 0.85, 0.85),
                               textAnchor='start'))

    def add_border(self, drawing):
        cover_left = (self.total_width + self.spine) / 2
        drawing.add(Rect(cover_left, 0,
                         self.margin, self.total_height,
                         fillColor=Color(0, .5, 0),
                         strokeColor=None))
        drawing.add(Rect(self.total_width - self.bleed - self.margin, 0,
                         self.margin, self.total_height,
                         fillColor=Color(0, .5, 0),
                         strokeColor=None))
        drawing.add(Rect(cover_left, self.bleed,
                         (self.total_width - self.spine) / 2, self.margin,
                         fillColor=Color(0, .5, 0),
                         strokeColor=None))
        drawing.add(Rect(cover_left, self.total_height - self.bleed - self.margin,
                         (self.total_width - self.spine) / 2, self.margin,
                         fillColor=Color(0, .5, 0),
                         strokeColor=None))

        drawing.add(Rect(self.bleed, 0,
                         self.margin, self.total_height,
                         fillColor=Color(0, .5, 0),
                         strokeColor=None))
        drawing.add(Rect((self.total_width - self.spine)/2-self.margin, 0,
                         self.margin, self.total_height,
                         fillColor=Color(0, .5, 0),
                         strokeColor=None))
        drawing.add(Rect(0, self.bleed,
                         (self.total_width - self.spine) / 2, self.margin,
                         fillColor=Color(0, .5, 0),
                         strokeColor=None))
        drawing.add(Rect(0, self.total_height - self.bleed - self.margin,
                         (self.total_width - self.spine) / 2, self.margin,
                         fillColor=Color(0, .5, 0),
                         strokeColor=None))

        # spine wiggle
        wiggle = 0.125*inch/2
        drawing.add(Rect((self.total_width-self.spine)/2, 0,
                         wiggle, self.total_height,
                         fillColor=Color(.5, 0, .5),
                         strokeColor=None))
        drawing.add(Rect((self.total_width+self.spine)/2-wiggle, 0,
                         wiggle, self.total_height,
                         fillColor=Color(.5, 0, .5),
                         strokeColor=None))

        # bar code
        bar_width = 3.622*inch
        bar_height = 1.26*inch
        drawing.add(Rect((self.total_width-self.spine)/2-self.margin-bar_width,
                         self.margin+self.bleed,
                         bar_width, bar_height,
                         fillColor=Color(.8, .8, .8),
                         strokeColor=None))


def live_main():
    drawing = Cover().draw()
    pil = renderPM.drawToPIL(drawing, bg=0x999999)
    image = LivePillowImage(pil)
    image.display((-pil.width/2, pil.height/2))
    Path('cover/cover_cropped.jpg').unlink()


def main():
    drawing = Cover().draw()
    renderPDF.drawToFile(drawing, "cover/cover.pdf")
    Path('cover/cover_cropped.jpg').unlink()


if __name__ == '__main__':
    main()
elif __name__ == '__live_coding__':
    live_main()
