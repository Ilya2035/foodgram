from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    CurrentUserView,
    LogoutView,
    ChangePasswordView,
    UserListView,
    UserDetailView
)

urlpatterns = [
    path('api/users/', RegisterView.as_view(), name='register'),
    path('api/auth/token/login/', LoginView.as_view(), name='token-login'),
    path('api/users/me/', CurrentUserView.as_view(), name='current-user'),
    path('api/auth/token/logout/', LogoutView.as_view(), name='token-logout'),
    path('api/users/set_password/', ChangePasswordView.as_view(), name='set-password'),
    path('api/users/', UserListView.as_view(), name='user-list'),
    path('api/users/<int:id>/', UserDetailView.as_view(), name='user-detail'),
]
