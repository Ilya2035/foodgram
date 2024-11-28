from django.urls import path
from .views import RegisterView

urlpatterns = [
    path('api/users/', RegisterView.as_view(), name='register'),
]
