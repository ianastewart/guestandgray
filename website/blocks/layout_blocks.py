from coderedcms.blocks import BaseLayoutBlock
from coderedcms.blocks.content_blocks import CarouselBlock
from django.utils.translation import gettext_lazy as _
from wagtail.core import blocks


class ItemGridBlock(BaseLayoutBlock):
    """
    Renders a row of item cards
    """

    fluid = blocks.BooleanBlock(
        required=False,
        label=_("Full width"),
    )

    child_css = blocks.CharBlock(
        max_length=255,
        required=False,
        label=("Child css"),
        help=("e.g. Use 'm-2' for a margin"),
    )

    class Meta:
        template = "website/blocks/item_grid_block.html"
        icon = "fa-th-large"
        label = _("Item Grid")
