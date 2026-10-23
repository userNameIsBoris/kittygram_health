from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Clinic(models.Model):
    name = models.CharField(max_length=120, unique=True)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.name


class HealthRecord(models.Model):
    VISIT = 'visit'
    PROCEDURE = 'procedure'
    TYPE_CHOICES = ((VISIT, 'Визит'), (PROCEDURE, 'Процедура'))
    PLANNED = 'planned'
    COMPLETED = 'completed'
    STATUS_CHOICES = ((PLANNED, 'Запланирована'), (COMPLETED, 'Завершена'))

    cat = models.ForeignKey('cats.Cat', on_delete=models.CASCADE,
                            related_name='health_records')
    clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL,
                               null=True, blank=True,
                               related_name='health_records')
    record_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    date = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES,
                              default=PLANNED)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('-date', '-id')

    def clean(self):
        super().clean()
        if (self.status == self.COMPLETED and self.date is not None
                and self.date > timezone.localdate()):
            raise ValidationError({'date': 'Завершённая запись не может быть в будущем.'})

    def __str__(self):
        return f'{self.get_record_type_display()}: {self.cat} — {self.date}'
