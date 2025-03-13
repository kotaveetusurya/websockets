# accounts/views.py
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import UserRegistrationForm

class SignUpView(CreateView):
    form_class = UserRegistrationForm  # Use the custom form
    success_url = reverse_lazy("login")  # Redirect to login page after successful registration
    template_name = "registration/signup.html"