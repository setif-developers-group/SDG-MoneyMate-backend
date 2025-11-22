from django.db import models
from django.contrib.auth.models import User

class AdvisorSession(models.Model):
    """
    Tracks user interactions with the Advisor Agent.
    Useful for analytics and improving recommendations over time.
    """
    QUERY_TYPES = [
        ('recommend', 'Product Recommendation'),
        ('analyze', 'Purchase Analysis'),
        ('compare', 'Product Comparison'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='advisor_sessions')
    query_type = models.CharField(max_length=50, choices=QUERY_TYPES)
    user_query = models.TextField(help_text="The user's original query")
    ai_response = models.TextField(help_text="The AI's response in Markdown format")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.query_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
