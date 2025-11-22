from django.urls import path
from .views import (
    ProductRecommendationView,
    PurchaseAnalysisView,
    ProductComparisonView,
    AdvisorHistoryView
)

urlpatterns = [
    path('recommend/', ProductRecommendationView.as_view(), name='advisor-recommend'),
    path('analyze-purchase/', PurchaseAnalysisView.as_view(), name='advisor-analyze'),
    path('compare/', ProductComparisonView.as_view(), name='advisor-compare'),
    path('history/', AdvisorHistoryView.as_view(), name='advisor-history'),
]