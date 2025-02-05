# Generated by Django 5.1.2 on 2025-02-05 11:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ticket", "0002_alter_ticket_options_remove_ticket_email_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ticket",
            name="closed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="closed_tickets",
                to="ticket.staff",
            ),
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("department", models.CharField(max_length=100)),
                ("program", models.CharField(max_length=100)),
                ("year_of_study", models.IntegerField(default=1)),
                ("date_joined", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="ticket",
            name="student",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="submitted_tickets",
                to="ticket.student",
            ),
        ),
    ]
