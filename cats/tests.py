from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .admin import CatAdminForm
from .models import Cat
from health.admin import HealthRecordAdminForm
from health.models import HealthRecord


class OwnershipAndAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.first = users.objects.create_user('first', password='testpass123')
        cls.second = users.objects.create_user('second', password='testpass123')
        cls.admin = users.objects.create_superuser('administrator', password='testpass123')
        cls.cat1 = Cat.objects.create(name='Первый', owner=cls.first, color='серый')
        cls.cat2 = Cat.objects.create(name='Второй', owner=cls.second, color='белый')
        cls.legacy = Cat.objects.create(name='Без владельца', color='чёрный')

    def test_lists_are_private_even_for_admin(self):
        client = APIClient()
        self.assertIn(client.get('/cats/').status_code, (401, 403))
        self.assertIn(client.post('/cats/', {'name': 'Гость', 'color': 'серый'}).status_code,
                      (401, 403))
        for user, expected in ((self.first, [self.cat1.pk]),
                               (self.second, [self.cat2.pk]), (self.admin, [])):
            client.force_authenticate(user)
            response = client.get('/cats/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual([cat['id'] for cat in response.data], expected)

    def test_owner_cannot_be_spoofed(self):
        client = APIClient()
        client.force_authenticate(self.second)
        response = client.post('/cats/', {'name': 'Новый', 'color': 'серый',
                                         'owner': self.first.pk}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['owner'], self.second.pk)
        self.assertEqual(Cat.objects.get(pk=response.data['id']).owner, self.second)

    def test_foreign_passport_all_operations_both_directions(self):
        client = APIClient()
        for owner, stranger, cat in ((self.first, self.second, self.cat1),
                                     (self.second, self.first, self.cat2)):
            record = HealthRecord.objects.create(cat=cat, date=timezone.localdate(),
                                                  record_type='visit')
            client.force_authenticate(stranger)
            listing = f'/api/cats/{cat.pk}/health-records/'
            detail = f'/api/health-records/{record.pk}/'
            self.assertEqual(client.get(listing).status_code, 404)
            self.assertEqual(client.post(listing, {'record_type': 'visit',
                'date': timezone.localdate().isoformat()}, format='json').status_code, 404)
            self.assertEqual(client.get(detail).status_code, 404)
            self.assertEqual(client.patch(detail, {'description': 'чужая'},
                                           format='json').status_code, 404)
            self.assertEqual(client.delete(detail).status_code, 404)
            self.assertEqual(client.post(detail + 'complete/').status_code, 404)
            record.refresh_from_db()
            self.assertEqual(record.status, 'planned')
            self.assertEqual(record.description, '')

    def test_admin_access_and_owner_required(self):
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.client.force_login(self.first)
        self.assertEqual(self.client.get('/admin/cats/cat/').status_code, 302)
        self.client.force_login(self.admin)
        for path in ('/admin/', '/admin/auth/user/', '/admin/cats/cat/',
                     '/admin/health/clinic/', '/admin/health/healthrecord/'):
            self.assertEqual(self.client.get(path).status_code, 200)
        response = self.client.get('/admin/cats/cat/')
        self.assertContains(response, 'Первый')
        self.assertContains(response, 'Второй')
        self.assertContains(response, 'Без владельца')
        form = CatAdminForm(data={'name': 'Новый', 'color': 'серый'})
        self.assertFalse(form.is_valid())
        self.assertIn('owner', form.errors)

    def test_admin_health_validation(self):
        today = timezone.localdate()
        data = {'cat': self.cat1.pk, 'record_type': 'visit',
                'date': (today + timedelta(days=1)).isoformat(),
                'status': 'completed', 'description': 'Осмотр'}
        form = HealthRecordAdminForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)
        record = HealthRecord.objects.create(cat=self.cat1, date=today,
                                              record_type='visit', status='completed')
        data.update(date=today.isoformat(), status='planned')
        form = HealthRecordAdminForm(data=data, instance=record)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
        record.refresh_from_db()
        data['status'] = 'completed'
        form = HealthRecordAdminForm(data=data, instance=record)
        self.assertTrue(form.is_valid(), form.errors)
