from wagtail.images.formats import Format, register_image_format
from django.utils.html import format_html


class CaptionedImageFormat(Format):
    def __init__(
        self,
        name,
        label,
        classnames,
        filter_spec,
        figure_classes,
        figcaption_classes="",
    ):
        super().__init__(name, label, classnames, filter_spec)
        self.figure_classes = figure_classes
        self.figcaption_classes = figcaption_classes

    def image_to_html(self, image, alt_text, extra_attributes=None):
        image_html = super().image_to_html(image, alt_text, extra_attributes)
        caption = image.item.name if image.item else alt_text
        caption_html = format_html(
            f"<figcaption class='small'>{caption}</figcaption>",
        )
        return format_html(
            f'<figure class="{self.figure_classes}">{image_html}{caption_html}</figure>'
        )


register_image_format(
    CaptionedImageFormat(
        "captioned",
        "Captioned left",
        "",
        "width-256",
        "card card-256l text-center",
    )
)
register_image_format(
    CaptionedImageFormat(
        "captioned_right",
        "Captioned right",
        "",
        "width-256",
        "card card-256r text-center",
    )
)
