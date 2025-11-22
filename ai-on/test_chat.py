import os
import django
import sys

# Setup Django environment
sys.path.append('/home/aymen/Desktop/dev/sdg_projects/ai-on-backend/ai-on')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth.models import User
from chat.services import process_chatbot_message

def test_function_calling():
    user = User.objects.get(username='aymen_user')
    
    # Test message that should trigger edit_user_profile
    message = "I got a raise! My new monthly income is 75000."
    
    print(f"Sending message: {message}")
    response = process_chatbot_message(user, message)
    
    print("\nResponse:")
    print(response)

if __name__ == "__main__":
    test_function_calling()
