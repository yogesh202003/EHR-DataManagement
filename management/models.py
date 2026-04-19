from django.db import models
from django.contrib.auth.models import AbstractUser

class PersonDetail(models.Model):
    GENDER_CHOLICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=GENDER_CHOLICES)
    dob = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    blood_group = models.CharField(max_length=10, null=True, blank=True)
    father_name = models.CharField(max_length=255, null=True, blank=True)
    mother_name = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    address_line1 = models.TextField(null=True, blank=True)
    allergies = models.TextField(null=True, blank=True)
    medical_notes = models.TextField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')

    # EHR Extension Fields
    emergency_contact_name = models.CharField(max_length=255, null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=15, null=True, blank=True)
    insurance_provider = models.CharField(max_length=255, null=True, blank=True)
    insurance_policy_number = models.CharField(max_length=100, null=True, blank=True)
    
    # Clinical Vitals
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    blood_pressure = models.CharField(max_length=20, null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    
    # Medical Background
    chronic_conditions = models.TextField(null=True, blank=True)
    current_medications = models.TextField(null=True, blank=True)
    assigned_doctor = models.CharField(max_length=255, null=True, blank=True)
    
    SMOKING_CHOICES = [
        ('Never', 'Never'),
        ('Former', 'Former'),
        ('Current', 'Current Smoker'),
    ]
    ALCOHOL_CHOICES = [
        ('None', 'None'),
        ('Occasional', 'Occasional'),
        ('Frequent', 'Frequent'),
    ]
    smoking_status = models.CharField(max_length=20, choices=SMOKING_CHOICES, default='Never')
    alcohol_consumption = models.CharField(max_length=20, choices=ALCOHOL_CHOICES, default='None')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.dob:
            from datetime import date
            today = date.today()
            self.age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Doctor', 'Doctor'),
        ('Patient', 'Patient'),
    ]
    person = models.OneToOneField(PersonDetail, on_delete=models.SET_NULL, null=True, blank=True, related_name='user')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Patient')
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Doctor(models.Model):
    AVAILABILITY_CHOICES = [
        ('Available', 'Available'),
        ('On Leave', 'On Leave'),
        ('In Surgery', 'In Surgery'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=255)
    experience_years = models.IntegerField(null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='Available')

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('No Show', 'No Show'),
    ]
    PRIORITY_CHOICES = [
        ('Normal', 'Normal'),
        ('Urgent', 'Urgent'),
        ('Emergency', 'Emergency'),
    ]
    patient = models.ForeignKey(PersonDetail, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    reason = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Normal')
    symptoms_summary = models.TextField(null=True, blank=True)
    is_virtual = models.BooleanField(default=False)
    meeting_link = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment: {self.patient.full_name} with {self.doctor}"

class MedicalReport(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
    ]
    patient = models.ForeignKey(PersonDetail, on_delete=models.CASCADE, related_name='medical_reports')
    report_type = models.CharField(max_length=100) # Blood Test, X-Ray, Scan
    report_date = models.DateField()
    summary_ai = models.TextField(null=True, blank=True)
    file_path = models.FileField(upload_to='medical_reports/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report: {self.report_type} for {self.patient.full_name}"

class MedicalHistory(models.Model):
    patient = models.ForeignKey(PersonDetail, on_delete=models.CASCADE, related_name='histories')
    condition_name = models.CharField(max_length=255)
    diagnosis_date = models.DateField(null=True, blank=True)
    treatment_plan = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.condition_name} - {self.patient.full_name}"

class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    instructions = models.TextField(null=True, blank=True)
    duration_days = models.IntegerField(default=7)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medication_name} for {self.appointment.patient.full_name}"

class InventoryItem(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    quantity = models.IntegerField(default=0)
    threshold = models.IntegerField(default=10)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('In', 'Stock In'),
        ('Out', 'Stock Out')
    ]
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} of {self.item.name}"

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled')
    ]
    patient = models.ForeignKey(PersonDetail, on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Unpaid')
    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invoice #{self.id} for {self.patient.full_name}"

class Payment(models.Model):
    METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Credit/Debit Card'),
        ('Online', 'Online Gateway (Mock)')
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Payment of {self.amount_paid} for Invoice #{self.invoice.id}"

class Message(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class SymptomCheck(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    symptoms = models.TextField()
    predicted_disease = models.CharField(max_length=255)
    probability = models.FloatField()
    suggested_specialization = models.CharField(max_length=255)
    medication = models.CharField(max_length=255, null=True, blank=True)
    dosage_instructions = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Symptom Check: {self.predicted_disease} ({self.probability}%)"
