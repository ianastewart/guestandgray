from django.forms import ModelForm, TextInput
from notes.models import Note


class NoteForm(ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content"]
        exclude = ["user"]
        widgets = {
            "tags": TextInput(
                attrs={
                    "data-role": "tagsinput",
                }
            ),
        }
