# Generated by Django 3.1 on 2022-06-18 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_reviewrating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviewrating',
            name='status',
            field=models.BooleanField(default=True),
        ),
    ]
