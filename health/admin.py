from django import forms
from django.contrib import admin

from .models import Clinic, HealthRecord


class HealthRecordAdminForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = '__all__'

    def clean(self):
        data = super().clean()
        if self.instance.pk:
            old_status = HealthRecord.objects.values_list('status', flat=True).get(
                pk=self.instance.pk)
            if (old_status == HealthRecord.COMPLETED
                    and data.get('status') == HealthRecord.PLANNED):
                self.add_error('status', 'Завершённую запись нельзя вернуть в план.')
        return data


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'phone')
    search_fields = ('name', 'address', 'phone')


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    form = HealthRecordAdminForm
    list_display = ('id', 'cat', 'owner', 'clinic', 'record_type', 'date', 'status')
    list_filter = ('cat__owner', 'status', 'record_type', 'clinic')
    search_fields = ('cat__name', 'cat__owner__username', 'description')
    list_select_related = ('cat__owner', 'clinic')

    @admin.display(description='Владелец')
    def owner(self, obj):
        return obj.cat.owner
