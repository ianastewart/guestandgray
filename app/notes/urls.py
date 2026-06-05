from django.urls import path
from notes.views import *

app_name = "notes"
urlpatterns = [
    path("list/", NoteListView.as_view(), name="list"),
    path("htmx/", NoteHtmxView.as_view(), name="htmx"),
    path("update/<int:pk>/", NoteHtmxView.as_view(), name="update"),
]
