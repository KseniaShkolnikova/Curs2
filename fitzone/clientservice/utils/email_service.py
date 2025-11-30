from datetime import timezone
import resend
from django.conf import settings
import os

# Настройка Resend
resend.api_key = os.getenv('RESEND_API_KEY', 'your-resend-api-key')

def send_resend_email(subject, html_content, to_email, text_content=None):
    """
    Отправка email через Resend
    """
    try:
        params = {
            'from': os.getenv('RESEND_FROM_EMAIL', 'FITZONE <onboarding@resend.dev>'),
            'to': [to_email],
            'subject': subject,
            'html': html_content,
        }
        
        # Добавляем текстовую версию если есть
        if text_content:
            params['text'] = text_content
        
        response = resend.Emails.send(params)
        print(f"Resend email sent successfully: {response}")
        return True
        
    except Exception as e:
        print(f"Resend error: {e}")
        return False

def send_subscription_email(user_email, subscription_name, price, order_number):
    """
    Отправка email о покупке абонемента
    """
    subject = f'Абонемент FITZONE - Оплата успешна!'
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .details {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
            .footer {{ margin-top: 20px; padding: 10px; text-align: center; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>FITZONE</h1>
            <h2>Абонемент успешно активирован!</h2>
        </div>
        
        <div class="content">
            <p>Уважаемый клиент!</p>
            <p>Ваш абонемент <strong>"{subscription_name}"</strong> успешно оплачен и активирован.</p>
            
            <div class="details">
                <h3>Детали заказа:</h3>
                <p><strong>Абонемент:</strong> {subscription_name}</p>
                <p><strong>Стоимость:</strong> {price} руб.</p>
                <p><strong>Номер заказа:</strong> {order_number}</p>
                <p><strong>Дата:</strong> {timezone.now().strftime('%d.%m.%Y %H:%M')}</p>
            </div>
            
            <p>Договор можно скачать в вашем профиле на сайте.</p>
        </div>
        
        <div class="footer">
            <p>Спасибо за выбор FITZONE!</p>
            <p>Телефон поддержки: +7 (495) 123-45-67</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Абонемент FITZONE - Оплата успешна!
    
    Уважаемый клиент!
    
    Ваш абонемент "{subscription_name}" успешно оплачен.
    
    Детали заказа:
    - Абонемент: {subscription_name}
    - Стоимость: {price} руб.
    - Номер заказа: {order_number}
    - Дата: {timezone.now().strftime('%d.%m.%Y %H:%M')}
    
    Договор можно скачать в вашем профиле на сайте.
    
    Спасибо за выбор FITZONE!
    """
    
    return send_resend_email(subject, html_content, user_email, text_content)