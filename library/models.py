from django.db import models


class LibraryEntry(models.Model):
    STATUS_WISHLIST = "wishlist"
    STATUS_PLAYING = "playing"
    STATUS_COMPLETED = "completed"
    STATUS_DROPPED = "dropped"

    STATUS_CHOICES = [
        (STATUS_WISHLIST, STATUS_WISHLIST),
        (STATUS_PLAYING, STATUS_PLAYING),
        (STATUS_COMPLETED, STATUS_COMPLETED),
        (STATUS_DROPPED, STATUS_DROPPED),
    ]

    external_game_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    hours_played = models.IntegerField()
