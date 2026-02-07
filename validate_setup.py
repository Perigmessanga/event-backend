#!/usr/bin/env python
"""
Validation script to check if all imports and models are correctly configured
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, os.path.dirname(__file__))

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# Test imports
try:
    from apps.authentication.models import CustomUser, OTPVerification
    print("✅ Authentication models imported successfully")
except Exception as e:
    print(f"❌ Authentication models import failed: {e}")

try:
    from apps.events.models import Event
    print("✅ Events models imported successfully")
except Exception as e:
    print(f"❌ Events models import failed: {e}")

try:
    from apps.orders.models import Order
    print("✅ Orders models imported successfully")
except Exception as e:
    print(f"❌ Orders models import failed: {e}")

try:
    from apps.payments.models import Payment
    print("✅ Payments models imported successfully")
except Exception as e:
    print(f"❌ Payments models import failed: {e}")

# Test Views
try:
    from apps.authentication.views import AuthViewSet, UserViewSet
    print("✅ Authentication views imported successfully")
except Exception as e:
    print(f"❌ Authentication views import failed: {e}")

try:
    from apps.events.views import EventViewSet
    print("✅ Events views imported successfully")
except Exception as e:
    print(f"❌ Events views import failed: {e}")

try:
    from apps.orders.views import OrderViewSet
    print("✅ Orders views imported successfully")
except Exception as e:
    print(f"❌ Orders views import failed: {e}")

try:
    from apps.payments.views import PaymentViewSet
    print("✅ Payments views imported successfully")
except Exception as e:
    print(f"❌ Payments views import failed: {e}")

print("\n✅ All imports validated successfully!")
