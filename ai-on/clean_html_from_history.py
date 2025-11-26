"""
Clean HTML Tags from Conversation History

This script removes HTML tags from all existing conversation history entries
for the chatbot agent. Run this if you have corrupted history with HTML tags.

Usage:
    python manage.py shell < clean_html_from_history.py
    
Or in Django shell:
    exec(open('clean_html_from_history.py').read())
"""

import re
from agents.models import agentModel, ConversationHistory

def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text.strip()

def clean_conversation_history():
    """Clean HTML tags from all chatbot conversation history."""
    try:
        # Get chatbot agent
        agent = agentModel.objects.get(name='chatbot_agent')
        
        # Get all conversation history for this agent
        conversations = ConversationHistory.objects.filter(agent=agent)
        
        cleaned_count = 0
        total_count = conversations.count()
        
        print(f"Found {total_count} conversation history entries to check...")
        
        for conv in conversations:
            # Check if content_data has parts with text
            if 'parts' in conv.content_data:
                modified = False
                for part in conv.content_data['parts']:
                    if 'text' in part and part['text']:
                        original_text = part['text']
                        cleaned_text = clean_html_tags(original_text)
                        
                        if original_text != cleaned_text:
                            part['text'] = cleaned_text
                            modified = True
                            print(f"Cleaned: '{original_text[:50]}...' -> '{cleaned_text[:50]}...'")
                
                if modified:
                    conv.save()
                    cleaned_count += 1
        
        print(f"\n✅ Cleaning complete!")
        print(f"   Total entries checked: {total_count}")
        print(f"   Entries cleaned: {cleaned_count}")
        print(f"   Entries unchanged: {total_count - cleaned_count}")
        
    except agentModel.DoesNotExist:
        print("❌ Error: chatbot_agent not found in database")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    clean_conversation_history()
