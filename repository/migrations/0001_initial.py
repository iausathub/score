# Generated by Django 4.0.10 on 2024-03-05 21:36

import django.contrib.postgres.fields
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Location",
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
                ("obs_lat_deg", models.FloatField(default=0)),
                ("obs_long_deg", models.FloatField(default=0)),
                ("obs_alt_m", models.FloatField(default=0)),
                (
                    "date_added",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date added"
                    ),
                ),
            ],
            options={
                "db_table": "location",
            },
        ),
        migrations.CreateModel(
            name="Satellite",
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
                ("sat_name", models.CharField(max_length=200)),
                ("sat_number", models.IntegerField(default=0)),
                (
                    "date_added",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date added"
                    ),
                ),
            ],
            options={
                "db_table": "satellite",
            },
        ),
        migrations.CreateModel(
            name="Observation",
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
                ("obs_time_utc", models.DateTimeField(verbose_name="observation time")),
                ("obs_time_uncert_sec", models.FloatField(default=0)),
                ("apparent_mag", models.FloatField(blank=True, null=True)),
                ("apparent_mag_uncert", models.FloatField(blank=True, null=True)),
                ("instrument", models.CharField(max_length=200)),
                (
                    "obs_mode",
                    models.CharField(
                        choices=[
                            ("VISUAL", "Visual"),
                            ("BINOCULARS", "Binoculars"),
                            ("CCD", "CCD"),
                            ("CMOS", "CMOS"),
                            ("OTHER", "Other"),
                        ],
                        max_length=200,
                    ),
                ),
                ("obs_filter", models.CharField(max_length=200)),
                ("obs_email", models.TextField()),
                (
                    "obs_orc_id",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=19),
                        default=list,
                        size=None,
                    ),
                ),
                ("sat_ra_deg", models.FloatField(blank=True, default=0, null=True)),
                (
                    "sat_ra_uncert_deg",
                    models.FloatField(blank=True, default=0, null=True),
                ),
                ("sat_dec_deg", models.FloatField(blank=True, default=0, null=True)),
                (
                    "sat_dec_uncert_deg",
                    models.FloatField(blank=True, default=0, null=True),
                ),
                (
                    "range_to_sat_km",
                    models.FloatField(blank=True, default=0, null=True),
                ),
                (
                    "range_to_sat_uncert_km",
                    models.FloatField(blank=True, default=0, null=True),
                ),
                (
                    "range_rate_sat_km_s",
                    models.FloatField(blank=True, default=0, null=True),
                ),
                (
                    "range_rate_sat_uncert_km_s",
                    models.FloatField(blank=True, default=0, null=True),
                ),
                ("comments", models.TextField(blank=True, null=True)),
                ("data_archive_link", models.TextField(blank=True, null=True)),
                ("flag", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "date_added",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date added"
                    ),
                ),
                (
                    "location_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="repository.location",
                    ),
                ),
                (
                    "satellite_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="repository.satellite",
                    ),
                ),
            ],
            options={
                "db_table": "observation",
            },
        ),
    ]
