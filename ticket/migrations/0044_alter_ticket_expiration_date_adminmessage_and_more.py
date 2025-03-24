# Generated by Django 5.1.2 on 2025-03-24 03:26

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0043_alter_ticket_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 23, 3, 26, 28, 467070, tzinfo=datetime.timezone.utc)),
        ),
        migrations.CreateModel(
            name='AdminMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admin_messages', to='ticket.ticket')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='StudentMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_messages', to='ticket.ticket')),
            ],
        ),
        migrations.DeleteModel(
            name='Message',
        ),
    ]
