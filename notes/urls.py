from django.urls import path
from notes.views import *

app_name = "notes"
urlpatterns = [
    path("list/", NoteListView.as_view(), name="list"),
    path("list/create/", NoteCreateView.as_view(), name="create"),
    path("list/update/<int:pk>/", NoteUpdateView.as_view(), name="update"),
    path("htmx/", NoteHtmxView.as_view(), name="htmx"),
]
