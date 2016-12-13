# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-12 22:27
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dbinv', '0002_auto_20161107_0840'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataVariable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('driver', models.CharField(max_length=255)),
                ('product', models.CharField(max_length=255)),
                ('band', models.CharField(max_length=255)),
                ('band_number', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feature_set', models.CharField(max_length=255)),
                ('count', models.IntegerField(blank=True, null=True)),
                ('date', models.DateField()),
                ('maximum', models.FloatField(blank=True, null=True)),
                ('mean', models.FloatField(blank=True, null=True)),
                ('skew', models.FloatField(blank=True, null=True)),
                ('minimum', models.FloatField(blank=True, null=True)),
                ('sd', models.FloatField(blank=True, null=True)),
                ('fid', models.IntegerField()),
                ('site', models.CharField(max_length=255)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dbinv.DataVariable')),
            ],
        ),
        migrations.CreateModel(
            name='Vector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geom', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('name', models.CharField(max_length=255)),
                ('attributes', django.contrib.postgres.fields.hstore.HStoreField()),
                ('site', models.CharField(blank=True, max_length=255, null=True)),
                ('source', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('fid', models.IntegerField()),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='vector',
            unique_together=set([('fid', 'source')]),
        ),
        migrations.AddField(
            model_name='result',
            name='vector',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dbinv.Vector'),
        ),
        migrations.AlterUniqueTogether(
            name='result',
            unique_together=set([('feature_set', 'date', 'product', 'site')]),
        ),
    ]
