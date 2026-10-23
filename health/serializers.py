from django.utils import timezone
from rest_framework import serializers

from .models import Clinic, HealthRecord


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ('id', 'name', 'address', 'phone')


class HealthRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthRecord
        fields = ('id', 'cat', 'clinic', 'record_type', 'date', 'status',
                  'description')
        read_only_fields = ('cat',)

    def validate(self, attrs):
        old = self.instance
        new_status = attrs.get('status', old.status if old else HealthRecord.PLANNED)
        new_date = attrs.get('date', old.date if old else None)
        if (new_status == HealthRecord.COMPLETED and new_date is not None
                and new_date > timezone.localdate()):
            raise serializers.ValidationError({
                'date': 'Завершённая запись не может быть в будущем.'
            })
        if old and old.status == HealthRecord.COMPLETED and 'status' in attrs:
            if attrs['status'] == HealthRecord.COMPLETED:
                raise serializers.ValidationError({
                    'status': 'Запись уже завершена.'
                })
            raise serializers.ValidationError({
                'status': 'Завершённую запись нельзя вернуть в план.'
            })
        return attrs
