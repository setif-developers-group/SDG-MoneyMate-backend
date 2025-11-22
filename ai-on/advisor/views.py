from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from .serializers import AdvisorQuerySerializer, AdvisorResponseSerializer, AdvisorSessionSerializer
from .services import process_product_recommendation, process_purchase_analysis, process_product_comparison
from .models import AdvisorSession


class ProductRecommendationView(APIView):
    """
    Get AI-powered product recommendations based on budget and preferences.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=AdvisorQuerySerializer,
        responses=AdvisorResponseSerializer,
        description="Get product recommendations based on your budget and preferences. The AI will suggest products that fit your financial situation."
    )
    def post(self, request):
        serializer = AdvisorQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        message = serializer.validated_data['message']
        result = process_product_recommendation(request.user, message)
        
        if result['type'] == 'error':
            return Response(result['data'], status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result['data'])


class PurchaseAnalysisView(APIView):
    """
    Analyze if a specific purchase fits your budget.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=AdvisorQuerySerializer,
        responses=AdvisorResponseSerializer,
        description="Analyze if a specific purchase is financially wise. The AI will consider your budget, spending patterns, and financial health."
    )
    def post(self, request):
        serializer = AdvisorQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        message = serializer.validated_data['message']
        result = process_purchase_analysis(request.user, message)
        
        if result['type'] == 'error':
            return Response(result['data'], status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result['data'])


class ProductComparisonView(APIView):
    """
    Compare multiple products and get a recommendation.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=AdvisorQuerySerializer,
        responses=AdvisorResponseSerializer,
        description="Compare multiple products and get AI-powered recommendations on which is the best choice for your budget."
    )
    def post(self, request):
        serializer = AdvisorQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        message = serializer.validated_data['message']
        result = process_product_comparison(request.user, message)
        
        if result['type'] == 'error':
            return Response(result['data'], status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result['data'])


class AdvisorHistoryView(APIView):
    """
    Get past advisor sessions.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses=AdvisorSessionSerializer(many=True),
        description="Retrieve your past advisor sessions and recommendations."
    )
    def get(self, request):
        sessions = AdvisorSession.objects.filter(user=request.user)
        serializer = AdvisorSessionSerializer(sessions, many=True)
        return Response(serializer.data)
