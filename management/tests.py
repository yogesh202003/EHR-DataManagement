from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import Mock, patch

from .models import Invoice, MedicalReport, PersonDetail, User
from . import ai_utils


class FeatureAvailabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin_test',
            password='pass123',
            role='Admin',
            is_staff=True,
        )
        self.patient = PersonDetail.objects.create(
            full_name='Test Patient',
            gender='Male',
            blood_group='O+',
            mobile_number='9999999999',
            email='test@example.com',
        )
        self.invoice = Invoice.objects.create(
            patient=self.patient,
            total_amount='1250.00',
            status='Paid',
        )
        self.report = MedicalReport.objects.create(
            patient=self.patient,
            report_type='Blood Test',
            report_date='2026-04-15',
            status='Reviewed',
            summary_ai='Hemoglobin and white cell counts are within expected range.',
            file_path=SimpleUploadedFile('report.txt', b'sample report content', content_type='text/plain'),
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_chatbot_page_loads(self):
        response = self.client.get(reverse('chatbot'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Database Chatbot')

    def test_chatbot_answer_endpoint_returns_fallback_response(self):
        response = self.client.post(
            reverse('ask_ai'),
            data='{"question": "How many patients are there?"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('answer', response.json())
        self.assertIn('patient records', response.json()['answer'])

    def test_symptom_checker_returns_analysis(self):
        response = self.client.post(reverse('symptom_checker'), {'symptoms': 'fever and cough'})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('disease', payload)
        self.assertIn('medication', payload)

    def test_provider_finder_api_returns_providers(self):
        response = self.client.get(reverse('api_nearby_healthcare'), {'lat': '13.0827', 'lon': '80.2707'})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('providers', payload)
        self.assertGreater(len(payload['providers']), 0)

    def test_billing_page_loads(self):
        response = self.client.get(reverse('billing_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invoice Central')

    def test_appointment_page_loads(self):
        response = self.client.get(reverse('appointment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Appointments')

    def test_invoice_downloads_are_generated(self):
        pdf_response = self.client.get(reverse('invoice_pdf', args=[self.invoice.id]))
        image_response = self.client.get(reverse('invoice_image', args=[self.invoice.id]))
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')
        self.assertEqual(image_response['Content-Type'], 'image/png')

    def test_report_downloads_are_generated(self):
        pdf_response = self.client.get(reverse('report_pdf', args=[self.report.id]))
        image_response = self.client.get(reverse('report_image', args=[self.report.id]))
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')
        self.assertEqual(image_response['Content-Type'], 'image/png')

    @patch('management.ai_utils.requests.Session')
    def test_live_provider_lookup_runs_without_remote_ai_flag(self, session_cls):
        fake_response = Mock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = {
            'elements': [
                {
                    'id': 101,
                    'lat': 13.0828,
                    'lon': 80.2708,
                    'tags': {
                        'name': 'Nearby Pharmacy',
                        'amenity': 'pharmacy',
                        'addr:street': 'Main Road',
                    }
                }
            ]
        }
        session = Mock()
        session.get.return_value = fake_response
        session_cls.return_value = session

        providers = ai_utils.get_nearby_healthcare(13.0827, 80.2707)

        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0]['name'], 'Nearby Pharmacy')
        session.get.assert_called()
