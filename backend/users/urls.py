from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    CurrentUserView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
    UpdateAvatarView,
    SubscriptionsView,
    SubscribeView
)

urlpatterns = [
    path('api/auth/token/login/', LoginView.as_view(), name='login'),
    path('api/auth/token/logout/', LogoutView.as_view(), name='token-logout'),
    path('api/users/', UserListView.as_view(), name='user-list'),
    path('api/users/<int:id>/', UserDetailView.as_view(), name='user-detail'),
    path('api/users/me/', CurrentUserView.as_view(), name='current-user'),
    path('api/users/me/avatar/', UpdateAvatarView.as_view(), name='update-avatar'),
    path('api/users/set_password/', ChangePasswordView.as_view(), name='set-password'),
    path('api/users/subscriptions/', SubscriptionsView.as_view(), name='subscriptions'),
    path('api/users/<int:id>/subscribe/', SubscribeView.as_view(), name='subscribe'),
]
