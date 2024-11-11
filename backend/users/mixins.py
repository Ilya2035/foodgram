from django.core.exceptions import PermissionDenied


class IsOwnerMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.get_object() != request.user:
            raise PermissionDenied("Вы не имеете права"
                                   " редактировать этот профиль.")
        return super().dispatch(request, *args, **kwargs)
