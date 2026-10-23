from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from cats.models import Cat
from .models import Clinic, HealthRecord


class HealthApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.owner = user_model.objects.create_user('owner', password='testpass123')
        cls.other = user_model.objects.create_user('other', password='testpass123')
        cls.admin = user_model.objects.create_user('admin', password='testpass123',
                                                    is_staff=True)
        cls.cat = Cat.objects.create(name='Мурка', color='серая', owner=cls.owner)
        cls.clinic = Clinic.objects.create(name='Ветклиника', address='ул. Мира, 1')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def test_owner_can_create_filter_paginate_and_complete(self):
        url = f'/api/cats/{self.cat.pk}/health-records/'
        today = timezone.localdate()
        for kind in ('visit', 'procedure'):
            response = self.client.post(url, {
                'clinic': self.clinic.pk, 'record_type': kind,
                'date': today.isoformat(), 'description': 'Осмотр',
            }, format='json')
            self.assertEqual(response.status_code, 201, response.data)
        response = self.client.get(url, {'type': 'visit', 'page_size': 1,
                                         'date_from': today.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        record_id = response.data['results'][0]['id']
        first_page = self.client.get(url, {'page_size': 1})
        self.assertEqual(first_page.data['count'], 2)
        self.assertIsNotNone(first_page.data['next'])
        second_page = self.client.get(url, {'page_size': 1, 'page': 2})
        self.assertNotEqual(first_page.data['results'][0]['id'],
                            second_page.data['results'][0]['id'])
        complete_url = f'/api/health-records/{record_id}/complete/'
        self.assertEqual(self.client.post(complete_url).status_code, 200)
        self.assertEqual(self.client.post(complete_url).status_code, 400)

    def test_future_completion_rejected(self):
        record = HealthRecord.objects.create(
            cat=self.cat, record_type='visit',
            date=timezone.localdate() + timedelta(days=1),
        )
        response = self.client.post(f'/api/health-records/{record.pk}/complete/')
        self.assertEqual(response.status_code, 400)
        record.refresh_from_db()
        self.assertEqual(record.status, 'planned')

    def test_other_user_cannot_read_or_change_records(self):
        record = HealthRecord.objects.create(
            cat=self.cat, record_type='visit', date=timezone.localdate(),
        )
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(
            f'/api/cats/{self.cat.pk}/health-records/').status_code, 404)
        detail = f'/api/health-records/{record.pk}/'
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.patch(detail, {'description': 'чужая правка'},
                                           format='json').status_code, 404)
        self.assertEqual(self.client.delete(detail).status_code, 404)

    def test_clinic_permissions(self):
        url = '/api/clinics/'
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {'name': 'Новая', 'address': 'Адрес'},
                                          format='json').status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(url, {'name': 'Новая', 'address': 'Адрес'},
                                          format='json').status_code, 201)

    def test_invalid_filters_and_unauthenticated_access(self):
        url = f'/api/cats/{self.cat.pk}/health-records/'
        self.assertEqual(self.client.get(url, {'type': 'other'}).status_code, 400)
        self.assertEqual(self.client.get(url, {'date_from': 'bad'}).status_code, 400)
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(url).status_code, (401, 403))
