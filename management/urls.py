from django.urls import path
from django.shortcuts import render
from .views import (
    LandingPageView, DashboardView, PersonListView, PersonDetailView, PersonCreateView, 
    PersonUpdateView, PersonDeleteView, ChatbotView, ask_ai, 
    LoginView, logout_view, AppointmentCreateView, AppointmentListView,
    MedicalReportCreateView, MedicalReportListView, review_report,
    BillingListView, InventoryListView,
    symptom_checker, telemedicine_room, generate_prescription, view_prescription, analytics_dashboard, PatientRegistrationView,
    nearby_healthcare_api, download_invoice_pdf, download_invoice_image, download_report_pdf, download_report_image,
    user_management
)
from . import api_views

urlpatterns = [
    path('', LandingPageView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', PatientRegistrationView.as_view(), name='register'),
    path('logout/', logout_view, name='logout'),
    path('persons/', PersonListView.as_view(), name='person_list'),
    path('persons/add/', PersonCreateView.as_view(), name='person_add'),
    path('persons/<int:pk>/', PersonDetailView.as_view(), name='person_view'),
    path('persons/<int:pk>/edit/', PersonUpdateView.as_view(), name='person_edit'),
    path('persons/<int:pk>/delete/', PersonDeleteView.as_view(), name='person_delete'),
    path('appointments/', AppointmentListView.as_view(), name='appointment_list'),
    path('appointments/book/', AppointmentCreateView.as_view(), name='appointment_book'),
    path('reports/', MedicalReportListView.as_view(), name='report_list'),
    path('reports/add/', MedicalReportCreateView.as_view(), name='report_add'),
    path('chatbot/', ChatbotView.as_view(), name='chatbot'),
    path('ask-ai/', ask_ai, name='ask_ai'),

    # API endpoints
    path('api/dashboard/', api_views.get_dashboard_data, name='api_dashboard'),
    path('api/patients/add/', api_views.add_patient_api, name='api_add_patient'),
    path('api/billing/', api_views.get_billing_data, name='api_billing'),
    path('api/payments/', api_views.process_payment_api, name='api_payments'),
    path('api/inventory/', api_views.get_inventory_data, name='api_inventory'),
    path('api/inventory/restock/', api_views.restock_inventory_api, name='api_restock'),
    path('api/nearby-healthcare/', nearby_healthcare_api, name='api_nearby_healthcare'),
    path('billing/invoices/<int:invoice_id>/pdf/', download_invoice_pdf, name='invoice_pdf'),
    path('billing/invoices/<int:invoice_id>/image/', download_invoice_image, name='invoice_image'),
    path('reports/<int:report_id>/pdf/', download_report_pdf, name='report_pdf'),
    path('reports/<int:report_id>/image/', download_report_image, name='report_image'),

    # New CMS Features
    path('symptom-checker/', symptom_checker, name='symptom_checker'),
    path('telemedicine/<int:appointment_id>/', telemedicine_room, name='telemedicine_room'),
    path('appointments/<int:appointment_id>/prescribe/', generate_prescription, name='generate_prescription'),
    path('prescriptions/<int:prescription_id>/', view_prescription, name='view_prescription'),
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('nearby-healthcare/', lambda r: render(r, 'management/nearby_healthcare.html'), name='nearby_healthcare'),
    path('reports/<int:report_id>/review/', review_report, name='review_report'),

    # Django Template Endpoints
    path('billing/', BillingListView.as_view(), name='billing_list'),
    path('inventory/', InventoryListView.as_view(), name='inventory_list'),
    path('users/', user_management, name='user_management'),
]
