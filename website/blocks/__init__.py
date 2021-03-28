from django.utils.translation import gettext_lazy as _
from coderedcms.blocks import (
    LAYOUT_STREAMBLOCKS,
    CONTENT_STREAMBLOCKS,
    HeroBlock,
    GridBlock,
    CardGridBlock,
    CardBlock,
)
from wagtail.core import blocks
from website.blocks.content_blocks import ItemImageBlock
from website.blocks.layout_blocks import ItemGridBlock

MY_CONTENT_STREAMBLOCKS = CONTENT_STREAMBLOCKS + [
    (
        "item_grid",
        ItemGridBlock(
            [
                ("item_image", ItemImageBlock()),
            ]
        ),
    ),
    ("item_image", ItemImageBlock()),
]

MY_LAYOUT_STREAMBLOCKS = [
    (
        "hero",
        HeroBlock(
            [
                ("row", GridBlock(MY_CONTENT_STREAMBLOCKS)),
                (
                    "cardgrid",
                    CardGridBlock(
                        [
                            ("card", CardBlock()),
                        ]
                    ),
                ),
                (
                    "itemgrid",
                    ItemGridBlock(
                        [
                            ("item_image", ItemImageBlock()),
                        ]
                    ),
                ),
                (
                    "html",
                    blocks.RawHTMLBlock(
                        icon="code", form_classname="monospace", label=_("HTML")
                    ),
                ),
            ]
        ),
    ),
    ("row", GridBlock(MY_CONTENT_STREAMBLOCKS)),
    (
        "cardgrid",
        CardGridBlock(
            [
                ("card", CardBlock()),
            ]
        ),
    ),
    (
        "itemgrid",
        ItemGridBlock(
            [
                ("item_image", ItemImageBlock()),
            ]
        ),
    ),
    (
        "html",
        blocks.RawHTMLBlock(icon="code", form_classname="monospace", label=_("HTML")),
    ),
]
