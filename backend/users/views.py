from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView
)
from django.urls import reverse_lazy
from .models import CustomUser
from subscriptions.models import Subscription
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .mixins import IsOwnerMixin


class UserListView(ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 10


class UserDetailView(DetailView):
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'


class UserCreateView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('login')


class UserUpdateView(LoginRequiredMixin, IsOwnerMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_detail')


class SubscriptionListView(LoginRequiredMixin, ListView):
    model = Subscription
    template_name = 'users/subscription_list.html'
    context_object_name = 'subscriptions'
    paginate_by = 10

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class SubscriptionCreateView(LoginRequiredMixin, CreateView):
    model = Subscription
    fields = []
    template_name = 'users/subscription_confirm.html'
    success_url = reverse_lazy('subscription_list')

    def form_valid(self, form):
        author = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        if self.request.user == author:
            form.add_error(None, 'Нельзя подписаться на самого себя.')
            return self.form_invalid(form)
        subscription, created = Subscription.objects.get_or_create(
            user=self.request.user,
            author=author
        )
        if not created:
            form.add_error(None, 'Вы уже подписаны на этого пользователя.')
            return self.form_invalid(form)
        return super().form_valid(form)


class SubscriptionDeleteView(LoginRequiredMixin, CreateView):
    model = Subscription
    fields = []
    template_name = 'users/subscription_confirm_delete.html'
    success_url = reverse_lazy('subscription_list')

    def post(self, request, *args, **kwargs):
        author = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        subscription = Subscription.objects.filter(
            user=self.request.user,
            author=author
        )
        if subscription.exists():
            subscription.delete()
        else:
            return self.handle_no_permission()
        return super().post(request, *args, **kwargs)