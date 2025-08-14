from django.db import models


class Place(models.Model):
    address = models.CharField(
        verbose_name='адрес',
        max_length=100,
        unique=True
    )
    latitude = models.FloatField(
        verbose_name='широта',
        null=True,
        blank=True
    )
    longitude = models.FloatField(
        verbose_name='долгота',
        null=True,
        blank=True
    )
    request_date = models.DateTimeField(
        verbose_name='дата запроса',
        null=True,
        blank=True,
        db_index=True,
        auto_now=True
    )

    class Meta:
        verbose_name = 'место'
        verbose_name_plural = 'места'

    def __str__(self):
        return f"{self.address}"
