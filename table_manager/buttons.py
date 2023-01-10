from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string


class BsButton:
    def __init__(
        self, content, button_type="", button_class="btn-primary", size="", href="", name="", value="", ajax=False
    ):
        self.content = content
        if button_type:
            self.button_type = button_type
        elif href:
            self.button_type = "link"
            self.href = href
        else:
            self.button_type = "submit"
        self.button_class = button_class
        self.size = size
        if name:
            self.name = "name"
        elif self.button_type != "link":
            self.name = f"submit_{slugify(content)}"
        self.value = value
        if ajax:
            if self.button_type == "submit":
                self.extra_classes = "js-submit"
            elif self.button_type == "post":
                self.button_type = "submit"
                self.extra_classes = "js-post"
            elif self.button_type == "link":
                self.extra_classes = "js-link"
            else:
                raise ValueError(f"button_type = {self.button_type} not supported")


class AjaxButton(BsButton):
    def __init__(self, *args, **kwargs):
        kwargs["ajax"] = True
        super().__init__(*args, **kwargs)


class Button:
    template_name = "table_manager/button.html"

    def __init__(self, content, name="", typ="button", css="btn btn-primary", **kwargs):
        self.context = {
            "element": "a" if kwargs.get("href") else "button",
            "content": content,
            "name": slugify(content) if not name else name,
            "class": css,
        }
        if self.context["element"] == "button":
            self.context["type"] = typ
        self.context.update(kwargs)

    def render(self):
        html = mark_safe(render_to_string(template_name=self.template_name, context=self.context))
        return html
