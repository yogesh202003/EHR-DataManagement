from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import PersonDetail, Appointment, MedicalReport, Invoice, Payment, InventoryItem, StockTransaction

def get_dashboard_data(request):
    try:
        total_patients = PersonDetail.objects.count()
        today_appointments = Appointment.objects.count() # Could filter by today
        pending_reports = MedicalReport.objects.filter(status='Pending').count()
        
        recent_patients_qs = PersonDetail.objects.order_by('-created_at')[:5]
        recent_patients = []
        for p in recent_patients_qs:
            recent_patients.append({
                'full_name': p.full_name,
                'status': p.status,
                'created_at': p.created_at.isoformat()
            })
            
        return JsonResponse({
            'stats': {
                'totalPatients': total_patients,
                'todayAppointments': today_appointments,
                'pendingReports': pending_reports
            },
            'recentPatients': recent_patients
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def add_patient_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            person = PersonDetail.objects.create(
                full_name=data.get('full_name', ''),
                mobile_number=data.get('phone', ''),
                city=data.get('city', ''),
                age=data.get('age', 0)
            )
            return JsonResponse({'success': True, 'id': person.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# --- Billing API ---
def get_billing_data(request):
    try:
        invoices = Invoice.objects.select_related('patient').order_by('-issued_date')[:10]
        data = []
        for inv in invoices:
            data.append({
                'id': inv.id,
                'patient_name': inv.patient.full_name,
                'amount': float(inv.total_amount),
                'status': inv.status,
                'issued_date': inv.issued_date.isoformat()
            })
        return JsonResponse({'invoices': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def process_payment_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invoice_id = data.get('invoice_id')
            amount = data.get('amount')
            method = data.get('method', 'Online')
            
            invoice = Invoice.objects.get(id=invoice_id)
            Payment.objects.create(
                invoice=invoice,
                amount_paid=amount,
                payment_method=method,
                transaction_id='MOCK_TXN_' + str(invoice_id)
            )
            invoice.status = 'Paid'
            invoice.save()
            return JsonResponse({'success': True, 'message': 'Payment processed successfully'})
        except Invoice.DoesNotExist:
             return JsonResponse({'error': 'Invoice not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# --- Inventory API ---
def get_inventory_data(request):
    try:
        items = InventoryItem.objects.all()
        data = []
        for item in items:
            data.append({
                'id': item.id,
                'name': item.name,
                'sku': item.sku,
                'quantity': item.quantity,
                'threshold': item.threshold,
                'price': float(item.price_per_unit)
            })
        return JsonResponse({'items': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def restock_inventory_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = data.get('quantity')
            
            item = InventoryItem.objects.get(id=item_id)
            item.quantity += quantity
            item.save()
            
            StockTransaction.objects.create(
                item=item,
                transaction_type='In',
                quantity=quantity,
                notes='Manual restock via API'
            )
            return JsonResponse({'success': True, 'new_quantity': item.quantity})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
