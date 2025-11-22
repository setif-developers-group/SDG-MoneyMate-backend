from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='budget.title', read_only=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'product_name', 'amount', 'category_name', 'description', 'date']

class ExpenseUploadSerializer(serializers.Serializer):
    message = serializers.CharField(
        required=False, 
        default='Process this expense.',
        help_text="Natural language description of the expense. AI will extract amount, category, and details."
    )
    file = serializers.FileField(
        required=False,
        help_text="Receipt image (JPEG, PNG) or PDF. AI will extract expense details from the file."
    )
