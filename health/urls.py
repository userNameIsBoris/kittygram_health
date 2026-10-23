from django.urls import path

from .views import CatHealthRecords, Clinics, CompleteHealthRecord, HealthRecordDetail


urlpatterns = [
    path('cats/<int:cat_id>/health-records/', CatHealthRecords.as_view()),
    path('health-records/<int:pk>/', HealthRecordDetail.as_view()),
    path('health-records/<int:pk>/complete/', CompleteHealthRecord.as_view()),
    path('clinics/', Clinics.as_view()),
]
