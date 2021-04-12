from django.utils.translation import gettext_lazy as _
from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

from coderedcms.blocks.base_blocks import BaseBlock


class ItemImageBlock(BaseBlock):
    """
    An image with a caption.
    """

    image = ImageChooserBlock(
        required=False,
        max_length=255,
        label=_("Image"),
    )
    caption = blocks.CharBlock(
        required=False,
        max_length=255,
        label=_("Title"),
        help_text=_("Leave blank for item name"),
    )

    show_caption = blocks.BooleanBlock(
        required=False,
        default=False,
        label=_("Show caption"),
        help_text=_("Show caption beneath the image"),
    )
    link_item = blocks.BooleanBlock(
        required=False,
        default=False,
        label=_("Link to item"),
        help_text=_("Link to item in shop"),
    )

    class Meta:
        template = "website/blocks/item_image_block.html"
        icon = "image"
        label = _("Item image")


class LinkBlock(BaseBlock):
    image = ImageChooserBlock(
        required=True,
        max_length=255,
        label=_("Image"),
    )
    title = blocks.CharBlock(
        required=False,
        max_length=100,
        label=_("Title"),
    )
    text = blocks.CharBlock(
        required=False,
        max_length=500,
        label=_("Text"),
    )
    link = blocks.CharBlock(
        required=False,
        max_length=100,
        label=_("Link"),
        help_text=_("Enter item or catalogue slug"),
    )

    class Meta:
        template = "website/blocks/link_block.html"
        icon = "image"
        label = _("Wide card")
