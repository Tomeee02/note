# Generated by Django 5.2.3 on 2025-06-18 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0003_note_height_note_width'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='position_x',
            field=models.IntegerField(default=100),
        ),
        migrations.AddField(
            model_name='board',
            name='position_y',
            field=models.IntegerField(default=100),
        ),
    ]
