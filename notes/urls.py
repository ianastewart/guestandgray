from django.urls import path
from notes.views import *

app_name = "notes"
notes_urls = [
    path("list/", NoteListView.as_view(), name="list"),
    path("list/create/", NoteCreateView.as_view(), name="create"),
    path("list/update/<int:pk>/", NoteUpdateView.as_view(), name="update"),
]
