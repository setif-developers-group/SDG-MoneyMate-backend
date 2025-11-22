from django.contrib import admin
from .models import AdvisorSession

@admin.register(AdvisorSession)
class AdvisorSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'query_type', 'created_at']
    list_filter = ['query_type', 'created_at']
    search_fields = ['user__username', 'user_query', 'ai_response']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
