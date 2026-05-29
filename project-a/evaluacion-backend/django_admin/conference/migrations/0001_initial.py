import uuid
import django.db.models.deletion
from django.db import migrations, models

def base_fields():
    return [
        ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
        ("created", models.DateTimeField(auto_now_add=True)),
        ("modified", models.DateTimeField(auto_now=True)),
    ]

class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL("CREATE SCHEMA IF NOT EXISTS content", migrations.RunSQL.noop),

        migrations.CreateModel(
            name="Conference",
            fields=base_fields() + [
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("timezone", models.CharField(max_length=50, default="UTC")),
            ],
            options={"db_table": '"content"."conference"', "ordering": ["-starts_at"]},
        ),

        migrations.CreateModel(
            name="Speaker",
            fields=base_fields() + [
                ("name", models.CharField(max_length=200)),
                ("affiliation", models.CharField(max_length=200, blank=True)),
                ("bio", models.TextField(blank=True)),
            ],
            options={"db_table": '"content"."speaker"', "ordering": ["name"]},
        ),

        migrations.CreateModel(
            name="Track",
            fields=base_fields() + [
                ("conference", models.ForeignKey(
                    "conference.Conference",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="tracks",
                )),
                ("name", models.CharField(max_length=100)),
                ("color", models.CharField(max_length=7, blank=True, default="#6f1d1b")),
                ("description", models.TextField(blank=True)),
            ],
            options={"db_table": '"content"."track"', "ordering": ["name"]},
        ),

        migrations.CreateModel(
            name="Session",
            fields=base_fields() + [
                ("track", models.ForeignKey(
                    "conference.Track",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="sessions",
                )),
                ("title", models.CharField(max_length=300)),
                ("abstract", models.TextField(blank=True)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("capacity", models.PositiveIntegerField(null=True, blank=True)),
            ],
            options={"db_table": '"content"."session"', "ordering": ["starts_at"]},
        ),

        migrations.CreateModel(
            name="SessionSpeaker",
            fields=base_fields() + [
                ("session", models.ForeignKey(
                    "conference.Session",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="session_speakers",
                )),
                ("speaker", models.ForeignKey(
                    "conference.Speaker",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="session_speakers",
                )),
            ],
            options={"db_table": '"content"."session_speaker"'},
        ),

        migrations.CreateModel(
            name="Registration",
            fields=base_fields() + [
                ("session", models.ForeignKey(
                    "conference.Session",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="registrations",
                )),
                ("user_email", models.EmailField(max_length=254)),
                ("status", models.CharField(
                    max_length=20,
                    choices=[
                        ("confirmed", "Confirmed"),
                        ("waitlist", "Waitlist"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="confirmed",
                )),
            ],
            options={"db_table": '"content"."registration"', "ordering": ["-created"]},
        ),

        migrations.AddField(
            model_name="Session",
            name="speakers",
            field=models.ManyToManyField(
                "conference.Speaker",
                through="conference.SessionSpeaker",
                related_name="sessions",
                blank=True,
            ),
        ),

        migrations.AlterUniqueTogether(
            name="SessionSpeaker",
            unique_together={("session", "speaker")},
        ),

        migrations.AddIndex(
            model_name="Registration",
            index=models.Index(fields=["session", "status"], name="reg_session_status_idx"),
        ),
    ]
