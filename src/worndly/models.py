from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="player_profile")
    name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse("worndly:profile_detail", args=[self.pk])
