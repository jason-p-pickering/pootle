# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0004_correct_checkerstyle_options_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='deserializers',
            field=models.CharField(max_length=255, null=True, verbose_name='Deserializers', blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='serializers',
            field=models.CharField(max_length=255, null=True, verbose_name='Serializers', blank=True),
        ),
    ]
