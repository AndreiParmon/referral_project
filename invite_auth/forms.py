from django.contrib.auth import login
from django.shortcuts import redirect
from django.views.generic import FormView
from django import forms
from invite_auth.models import User
import random

from invite_auth.views import PhoneForm

auth_codes = {}


class CodeForm(forms.Form):
    phone = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(label='Код из СМС')


class CodeVerifyView(FormView):
    template_name = 'verify.html'
    form_class = CodeForm

    def get_initial(self):
        initial = super().get_initial()
        initial['phone'] = self.request.GET.get('phone')
        return initial

    def form_valid(self, form):
        phone = form.cleaned_data['phone']
        code = form.cleaned_data['code']

        print(f"Phone: {phone}, Code: {code}")

        real_code = auth_codes.get(phone)
        if real_code != code:
            form.add_error('code', 'Неверный код')
            return self.form_invalid(form)

        user, _ = User.objects.get_or_create(phone=phone)
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        auth_codes.pop(phone, None)

        return redirect('profile')


class PhoneLoginView(FormView):
    template_name = 'login.html'
    form_class = PhoneForm

    def form_valid(self, form):
        phone = form.cleaned_data['phone'].replace(" ", "")
        code = f"{random.randint(1000, 9999)}"
        auth_codes[phone] = code
        print(f"[WEB DEBUG] {phone} → код: {code}")
        return redirect(f'/verify/?phone={phone}')
