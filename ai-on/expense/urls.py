from django.urls import path
from .views import ExpenseListCreateView, ReportView

urlpatterns = [
    path('', ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('report/', ReportView.as_view(), name='expense-report'),
]
