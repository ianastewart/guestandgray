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
        if image.item:
            if alt_text == "No caption":
                caption = ""
                alt_text = image.item.name
            elif alt_text[:6] == "Figure":
                caption = f"{alt_text}. {image.item.name}"
                alt_text = caption
            else:
                caption = image.item.name
        else:
            caption = alt_text
        if caption:
            caption_html = format_html(
                f"<figcaption class='small'>{caption}</figcaption>",
            )
        else:
            caption_html = ""
        image_html = super().image_to_html(image, alt_text, extra_attributes)
        if image.item:
            image_html = f'<a href="/item/{image.item.ref}">{image_html}</a>'
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
