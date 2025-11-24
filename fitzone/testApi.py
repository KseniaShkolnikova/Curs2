# test_api_subscription.py
import os
import django
import sys
from datetime import date
import requests
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitzone.settings')
django.setup()

from django.contrib.auth.models import User
from clientservice.models import SubscriptionTypes, Subscriptions, UserProfiles

def test_api_subscription():
    """
    ТЕСТ: Создание через API → Проверка в БД
    """
    print("ТЕСТ: СОЗДАНИЕ ЧЕРЕЗ API → ПРОВЕРКА В БД")
    print("=" * 50)
    
    user = User.objects.get_or_create(
        username='api_test_user',
        defaults={'email': 'api_test@example.com', 'is_active': True}
    )[0]
    
    sub_type = SubscriptionTypes.objects.first()
    if not sub_type:
        print("❌ Нет типов абонементов")
        return
    
    api_data = {
        'user_id': user.id, 
        'subscriptiontype_id': sub_type.id, 
        'startdate': date.today().isoformat(),
        'is_active': True
    }
    
    print(f"   URL: http://localhost:8000/api/subscriptions/")
    print(f"   Данные: {api_data}")
    
    try:
        response = requests.post(
            'http://localhost:8000/api/subscriptions/',
            json=api_data,
            headers={'Content-Type': 'application/json'},
            auth=('sesha', '1')
        )
        
        print(f"📥 Ответ API: статус {response.status_code}")
        
        if response.status_code == 201:
            api_response = response.json()
            subscription_id = api_response.get('id')
            print(f"API успешно создал абонемент ID: {subscription_id}")
            
            # 4. ПРОВЕРЯЕМ В БАЗЕ ДАННЫХ
            try:
                db_subscription = Subscriptions.objects.get(id=subscription_id)
                print("Абонемент создан через API и найден в БД")
                print(f"   ID: {db_subscription.id}")
                print(f"   Пользователь: {db_subscription.user.username}")
                print(f"   Тип: {db_subscription.subscriptiontype.name}")
                print(f"   Дата: {db_subscription.startdate}")
                print(f"   Активен: {db_subscription.is_active}")
                
            except Subscriptions.DoesNotExist:
                print("ТЕСТ ПРОВАЛЕН: API вернул успех, но абонемента нет в БД")
                
        else:
            print(f"Ошибка API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"Ошибка подключения к API: {e}")

if __name__ == "__main__":
    test_api_subscription()