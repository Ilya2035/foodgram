from django.urls import path
from .views import (
    UserListView, UserDetailView, UserCreateView, UserUpdateView,
    SubscriptionListView, SubscriptionCreateView, SubscriptionDeleteView
)

urlpatterns = [
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/register/', UserCreateView.as_view(), name='user_register'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('subscriptions/', SubscriptionListView.as_view(),
         name='subscription_list'),
    path('subscriptions/add/<int:pk>/', SubscriptionCreateView.as_view(),
         name='subscription_add'),
    path('subscriptions/delete/<int:pk>/', SubscriptionDeleteView.as_view(),
         name='subscription_delete'),
]
