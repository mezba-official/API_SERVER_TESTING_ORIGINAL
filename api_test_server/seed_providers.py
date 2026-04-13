import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_test_server.settings')
django.setup()

from api_set1.models import InsuranceProvider

def seed_providers():
    providers = [
        {
            "name": "DIC Insurance Broker UAE",
            "code": "dic-broker-uae",
            "api_base_url": "https://api.dicuae.com/v1",
            "api_key": "dic_uae_test_key_001",
            "provider_class_path": "api_set1.services.providers.DIC.DICProvider",
            "icon_name": "fas fa-handshake"
        },
        {
            "name": "NIA UAE",
            "code": "nia-uae",
            "api_base_url": "https://api.uae-insurance.com/v1",
            "api_key": "uae_nia_test_key_456",
            "provider_class_path": "api_set1.services.providers.NID.ICICIProvider",
            "icon_name": "fas fa-building"
        },
        {
            "name": "QIC Insurance UAE",
            "code": "qic-uae",
            "api_base_url": "https://api.qic.com.qa/v1",
            "api_key": "qic_test_key_789",
            "provider_class_path": "api_set1.services.providers.QIC.QICProvider",
            "icon_name": "fas fa-shield-alt"
        }
    ]

    for p_data in providers:
        obj, created = InsuranceProvider.objects.get_or_create(
            code=p_data['code'],
            defaults=p_data
        )
        if created:
            print(f"Created provider: {p_data['name']}")
        else:
            print(f"Provider already exists: {p_data['name']}")

if __name__ == "__main__":
    seed_providers()
