# Generated by Django 5.1.4 on 2025-02-11 09:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog_generator', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='blogpost',
            old_name='youtue_link',
            new_name='youtube_link',
        ),
    ]
