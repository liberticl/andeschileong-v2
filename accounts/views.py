from django.contrib.auth.views import LoginView
import requests
from ciudadespendientes.utils import get_client_ip, get_location_from_ip


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_ip = get_client_ip(self.request)
        context.update(get_location_from_ip(client_ip))
        return context
