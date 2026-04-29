from django.conf import settings
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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="library_entries",
    )
    external_game_id = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    hours_played = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "external_game_id"],
                name="unique_library_entry_per_user_game",
            ),
        ]

    def external_id_length(self):
        if self.external_game_id is None:
            return 0
        return len(self.external_game_id)

    def external_id_upper(self):
        if self.external_game_id is None:
            return ""
        return self.external_game_id.upper()

    def hours_played_label(self):
        if self.hours_played <= 0:
            return "none"
        if self.hours_played < 10:
            return "low"
        return "high"

    def status_value(self):
        values = {
            self.STATUS_WISHLIST: 0,
            self.STATUS_PLAYING: 1,
            self.STATUS_COMPLETED: 2,
            self.STATUS_DROPPED: 3,
        }
        return values.get(self.status, -1)
