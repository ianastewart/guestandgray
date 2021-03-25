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

MY_CONTENT_STREAMBLOCKS = CONTENT_STREAMBLOCKS + [
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
        "html",
        blocks.RawHTMLBlock(icon="code", form_classname="monospace", label=_("HTML")),
    ),
]
