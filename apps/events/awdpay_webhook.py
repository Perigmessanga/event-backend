# apps/events/awdpay_webhook.py
from apps.events.models import EventRegistration

def mark_payment_success(custom_identifier: str, trx_id: str):
    try:
        registration = EventRegistration.objects.get(custom_identifier=custom_identifier)
        registration.payment_status = 'paid'
        registration.awdpay_trx_id = trx_id
        registration.save()
        print(f"Payment marked as successful for {custom_identifier}")
    except EventRegistration.DoesNotExist:
        print(f"No registration found with custom_identifier={custom_identifier}")