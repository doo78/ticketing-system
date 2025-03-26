import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0026_alter_ticket_expiration_date'),
        ('ticket', '0026_merge_20250323_0017'),

    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 19, 23, 40, 24, 329713, tzinfo=datetime.timezone.utc)),

            field=models.DateTimeField(default=datetime.datetime(2025, 4, 22, 0, 17, 24, 598922, tzinfo=datetime.timezone.utc)),

        ),
    ]
