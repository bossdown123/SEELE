# Generated by Django 5.0.7 on 2024-07-28 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("router", "0003_alter_order_asset_id_alter_order_symbol"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="order_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("market", "market"),
                    ("limit", "limit"),
                    ("stop", "stop"),
                    ("stop_limit", "stop_limit"),
                    ("trailing_stop", "trailing_stop"),
                ],
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="side",
            field=models.CharField(
                blank=True,
                choices=[("buy", "buy"), ("sell", "sell")],
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="time_in_force",
            field=models.CharField(
                blank=True,
                choices=[
                    ("gtc", "gtc"),
                    ("day", "day"),
                    ("opg", "opg"),
                    ("cls", "cls"),
                    ("ioc", "ioc"),
                    ("fok", "fok"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
