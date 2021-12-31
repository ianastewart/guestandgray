from django.db import models
from shop.models import Item
from django.contrib.auth.models import User
from taggit.managers import TaggableManager


class Note(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager()
    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        if self.item:
            return f"{self.item.ref} {self.title}"
        return self.title
