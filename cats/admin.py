from django import forms
from django.contrib import admin

from .models import Cat


class CatAdminForm(forms.ModelForm):
    class Meta:
        model = Cat
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owner'].required = True


@admin.register(Cat)
class CatAdmin(admin.ModelAdmin):
    form = CatAdminForm
    list_display = ('id', 'name', 'owner', 'color', 'birth_year')
    list_filter = ('owner', 'birth_year')
    search_fields = ('name', 'owner__username')
    list_select_related = ('owner',)
