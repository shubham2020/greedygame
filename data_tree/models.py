from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)


class Device(models.Model):
    name = models.CharField(max_length=20)


class Metrics(models.Model):
    web_req = models.PositiveIntegerField(default=0)
    time_spent = models.PositiveIntegerField(default=0)
    device = models.ForeignKey(Device, on_delete=models.CASCADE,
                               related_name='metrics_device')
    country = models.ForeignKey(Country, on_delete=models.CASCADE,
                                related_name='metrics_country')
