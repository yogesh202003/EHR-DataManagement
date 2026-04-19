import os
import django
import random
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare_chatbot.settings')
django.setup()

from management.models import PersonDetail, User, Doctor, Appointment, InventoryItem, Invoice, Payment, MedicalHistory, Prescription, SymptomCheck

def seed_data():
    print("Seeding database with professional CMS data...")

    # 1. Create Admin if none exists
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@ehrdata.com', 'admin123')
        admin.role = 'Admin'
        admin.save()
        print("Admin user created: admin / admin123")

    # 2. Create Doctors
    specializations = ['General Physician', 'Cardiologist', 'Neurologist', 'Gastroenterologist', 'Pediatrician']
    doctors = []
    for spec in specializations:
        username = spec.lower().replace(' ', '_')
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username, f'{username}@clinic.com', 'doctor123')
            user.role = 'Doctor'
            user.save()
            dr = Doctor.objects.create(
                user=user,
                specialization=spec,
                experience_years=random.randint(5, 20),
                qualification='MBBS, MD'
            )
            doctors.append(dr)
    
    if not doctors:
        doctors = list(Doctor.objects.all())

    # 3. Create Patients
    if not PersonDetail.objects.exists():
        patients_data = [
            {'full_name': 'Johnathan Miller', 'gender': 'Male', 'age': 45, 'blood_group': 'A+', 'city': 'New York', 'status': 'Active', 'email': 'john@example.com'},
            {'full_name': 'Sarah Williams', 'gender': 'Female', 'age': 32, 'blood_group': 'O-', 'city': 'Los Angeles', 'status': 'Active', 'email': 'sarah@example.com'},
            {'full_name': 'Michael Chen', 'gender': 'Male', 'age': 58, 'blood_group': 'B+', 'city': 'Chicago', 'status': 'Active', 'email': 'michael@example.com'},
            {'full_name': 'Ariana Grande', 'gender': 'Female', 'age': 28, 'blood_group': 'AB+', 'city': 'Miami', 'status': 'Active', 'email': 'ariana@example.com'},
        ]
        for p_data in patients_data:
            p = PersonDetail.objects.create(**p_data)
            # Create a user account for each patient
            uname = p.full_name.split(' ')[0].lower() + str(p.id)
            if not User.objects.filter(username=uname).exists():
                u = User.objects.create_user(uname, p.email, 'patient123')
                u.role = 'Patient'
                u.person = p
                u.save()
                print(f"Patient user created: {uname} / patient123")

    patients = list(PersonDetail.objects.all())

    # 4. Create Appointments with Priority
    if not Appointment.objects.exists():
        for i in range(10):
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=datetime.now() + timedelta(days=random.randint(0, 7), hours=random.randint(0, 23)),
                reason=random.choice(['Routine Checkup', 'Fever', 'Heart ache', 'Stomach pain']),
                priority=random.choice(['Normal', 'Urgent', 'Emergency']),
                status='Scheduled',
                is_virtual=random.choice([True, False])
            )

    # 5. Create Inventory
    if not InventoryItem.objects.exists():
        items = [
            {'name': 'Paracetamol', 'sku': 'MED-01', 'quantity': 500, 'price_per_unit': 0.50},
            {'name': 'Insulin', 'sku': 'MED-02', 'quantity': 50, 'price_per_unit': 25.00},
            {'name': 'Blood Pressure Monitor', 'sku': 'DEV-01', 'quantity': 10, 'price_per_unit': 45.00},
        ]
        for item in items:
            InventoryItem.objects.create(**item)

    # 6. Create Symptom Checks for Analytics
    if not SymptomCheck.objects.exists():
        for i in range(20):
            SymptomCheck.objects.create(
                symptoms="Fever and Cough",
                predicted_disease=random.choice(['Flu', 'Cold', 'COVID-19', 'Gastritis', 'Migraine']),
                probability=random.randint(60, 95),
                suggested_specialization=random.choice(['General Physician', 'Neurologist'])
            )

    print("Success: Database seeded with professional clinic data.")

if __name__ == "__main__":
    seed_data()
