# Generated by Django 5.1.2 on 2025-03-25 18:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0048_alter_ticket_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 24, 18, 0, 35, 338436, tzinfo=datetime.timezone.utc)),
        ),
    ]
