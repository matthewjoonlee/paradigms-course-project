from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class PlayerProfile(models.Model):
    # Keep player-specific fields separate from Django's built-in auth model.
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

class Game(models.Model):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German"),
        ("pt", "Portuguese"),
    ]

    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name="games")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    target_word = models.CharField(max_length=5)
    won = models.BooleanField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.player.username} - {self.language} - {self.created_at.date()}"

class Guess(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="guesses")
    word = models.CharField(max_length=5)
    result = models.CharField(max_length=5)  # G=green, Y=yellow, X=gray e.g. "GXYXG"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.word} -> {self.result}"
