from django.contrib import admin
from .models import PersonDetail, User, Doctor, Appointment, MedicalReport, Invoice, Payment, InventoryItem, MedicalHistory, Prescription

@admin.register(PersonDetail)
class PersonDetailAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'blood_group', 'city', 'status')
    search_fields = ('full_name', 'city', 'mobile_number')
    list_filter = ('gender', 'blood_group', 'status')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'person')
    search_fields = ('username', 'email')
    list_filter = ('role',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'availability_status')
    search_fields = ('user__username', 'specialization')
    list_filter = ('availability_status',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'status', 'is_virtual')
    search_fields = ('patient__full_name', 'doctor__user__username')
    list_filter = ('status', 'appointment_date', 'is_virtual')

@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('patient', 'report_type', 'report_date', 'status')
    search_fields = ('patient__full_name', 'report_type')
    list_filter = ('status', 'report_date')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('patient', 'total_amount', 'status', 'issued_date')
    list_filter = ('status', 'issued_date')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount_paid', 'payment_date', 'payment_method')

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'threshold', 'price_per_unit')

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'condition_name', 'diagnosis_date')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'medication_name', 'dosage', 'duration_days')
