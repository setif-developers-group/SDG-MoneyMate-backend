from rest_framework import serializers
from .models import AdvisorSession

class AdvisorQuerySerializer(serializers.Serializer):
    """
    Serializer for incoming advisor queries.
    """
    message = serializers.CharField(
        required=True,
        help_text="Natural language query for the advisor (e.g., 'Recommend a laptop under 50000 DZD')"
    )

class AdvisorResponseSerializer(serializers.Serializer):
    """
    Serializer for advisor responses.
    """
    advice = serializers.CharField(
        help_text="AI-generated advice in Markdown format"
    )
    session_id = serializers.IntegerField(
        required=False,
        help_text="ID of the advisor session for tracking"
    )

class AdvisorSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving past advisor sessions.
    """
    class Meta:
        model = AdvisorSession
        fields = ['id', 'query_type', 'user_query', 'ai_response', 'created_at']
        read_only_fields = ['id', 'created_at']
