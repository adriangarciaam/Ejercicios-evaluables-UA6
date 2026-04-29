from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def assign_existing_entries_to_demo_user(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    LibraryEntry = apps.get_model("library", "LibraryEntry")

    if not LibraryEntry.objects.filter(user__isnull=True).exists():
        return

    demo_user, _ = User.objects.get_or_create(
        username="demo",
        defaults={"password": make_password(None)},
    )
    LibraryEntry.objects.filter(user__isnull=True).update(user=demo_user)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("library", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="libraryentry",
            name="external_game_id",
            field=models.CharField(max_length=255),
        ),
        migrations.AddField(
            model_name="libraryentry",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="library_entries",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            assign_existing_entries_to_demo_user,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="libraryentry",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="library_entries",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="libraryentry",
            constraint=models.UniqueConstraint(
                fields=("user", "external_game_id"),
                name="unique_library_entry_per_user_game",
            ),
        ),
    ]
