# Generated by Django 5.1.2 on 2024-11-12 02:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cargainscripcion',
            name='Ciclo',
            field=models.CharField(default='01-2024', max_length=20),
            preserve_default=False,
        ),
    ]
