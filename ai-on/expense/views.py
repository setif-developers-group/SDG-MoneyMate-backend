from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Expense
from .serializers import ExpenseSerializer, ExpenseUploadSerializer
from .services import process_expense_management, process_report_generation
from django.core.files.storage import default_storage
from drf_spectacular.utils import extend_schema
import os

class ExpenseListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        expenses = Expense.objects.filter(user=request.user).order_by('-date')
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=ExpenseUploadSerializer,
        responses=ExpenseSerializer(many=True),
        description="Upload an expense via natural language message or receipt file (image/PDF). AI will automatically extract amount, category, product name, and description."
    )
    def post(self, request):
        message = request.data.get('message', 'Process this expense.')
        file_obj = request.FILES.get('file')
        
        file_path = None
        if file_obj:
            # Save file temporarily
            file_name = default_storage.save(f"temp/{file_obj.name}", file_obj)
            file_path = default_storage.path(file_name)
            
        # Process with AI - no manual data
        result = process_expense_management(request.user, message, file_path, manual_data=None)
        
        # Clean up temp file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        if result['type'] == 'error':
            return Response(result['data'], status=status.HTTP_400_BAD_REQUEST)
            
        return Response(result['data'], status=status.HTTP_201_CREATED)

class ReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message = request.data.get('message', 'Generate a full financial report.')
        result = process_report_generation(request.user, message)
        
        if result['type'] == 'error':
            return Response(result['data'], status=status.HTTP_400_BAD_REQUEST)
            
        return Response(result['data'])
