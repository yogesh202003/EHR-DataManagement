import os
import django
from django.db import transaction
from django.utils import timezone

# -------------------------------
# DJANGO SETUP
# -------------------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare_chatbot.settings')

try:
    django.setup()
except Exception as e:
    print("Error setting up Django:", e)
    exit()

# -------------------------------
# IMPORT MODELS
# -------------------------------
from management.models import PersonDetail, Invoice, Payment


def test_billing_execution():
    print("\n--- 🚀 Billing Execution Test Started ---\n")

    try:
        with transaction.atomic():

            # 1. Get or create patient safely
            patient, created = PersonDetail.objects.get_or_create(
                full_name="Test Patient",
                defaults={
                    'gender': "Male",
                    'dob': timezone.now().date()
                }
            )

            print(f"👤 Patient: {patient.full_name} | Created: {created}")

            # 2. Create Invoice
            invoice = Invoice.objects.create(
                patient=patient,
                total_amount=1250.00,
                status='Unpaid'
            )

            print(f"🧾 Invoice Created: #INV-{invoice.id} | Amount: ₹{invoice.total_amount}")

            # 3. Process Payment
            payment = Payment.objects.create(
                invoice=invoice,
                amount_paid=1250.00,
                payment_method='Cash'
            )

            # 4. Update Invoice Status
            invoice.status = 'Paid'
            invoice.save()

            print(f"💰 Payment Done: ₹{payment.amount_paid} via {payment.payment_method}")
            print(f"✅ Final Invoice Status: {invoice.status}")

        print("\n🎉 SUCCESS: Billing logic is fully operational.\n")

    except Exception as e:
        print("\n❌ ERROR during billing execution:")
        print(str(e))


# -------------------------------
# RUN SCRIPT
# -------------------------------
if __name__ == "__main__":
    test_billing_execution()