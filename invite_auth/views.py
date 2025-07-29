import random

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView
from django import forms
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated

from invite_auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
import random, time

from invite_auth.serializers import RequestCodeSerializer, VerifyCodeSerializer, ProfileSerializer, \
    ActivateInviteCodeSerializer

auth_codes = {}


@extend_schema(
    request=RequestCodeSerializer,
    responses={200: OpenApiResponse(description='Код отправлен')},
)
class RequestCodeView(APIView):
    def post(self, request):
        serializer = RequestCodeSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            time.sleep(2)
            code = f"{random.randint(1000, 9999)}"
            auth_codes[phone] = code
            print(f"[DEBUG] {phone} → код: {code}")
            return Response({'message': 'Код отправлен'})
        return Response(serializer.errors, status=400)


class VerifyCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            code = serializer.validated_data['code']
            real_code = auth_codes.get(phone)
            if not real_code:
                return Response({'error': 'Код не запрашивался!'}, status=400)
            if code != real_code:
                return Response({'error': 'Неверный код!'}, status=400)
            user, created = User.objects.get_or_create(phone=phone)
            token, _ = Token.objects.get_or_create(user=user)
            del auth_codes[phone]
            return Response({'token': token.key, 'new_user': created})
        return Response(serializer.errors, status=400)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


class ActivateInviteCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.used_invite_code:
            return Response({"detail": "Инвайт-Код уже активирован."}, status=400)

        serializer = ActivateInviteCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['invite_code']

        try:
            inviter = User.objects.get(invite_code=code)
        except User.DoesNotExist:
            return Response({"detail": "Инвайт-Код не найден."}, status=400)

        if inviter == user:
            return Response({"detail": "Вы не можете активировать свой собственный инвайт-код."}, status=400)

        user.used_invite_code = code
        user.save()
        inviter.invited_users.add(user)

        return Response({"detail": "Инвайт-код активирован."}, status=200)


class PhoneForm(forms.Form):
    phone = forms.CharField(label='Номер телефона')


class CodeForm(forms.Form):
    phone = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(label='Код из СМС')


class PhoneLoginView(FormView):
    template_name = 'login.html'
    form_class = PhoneForm

    def form_valid(self, form):
        phone = form.cleaned_data['phone'].replace(" ", "")
        code = f"{random.randint(1000, 9999)}"
        auth_codes[phone] = code
        print(f"[WEB DEBUG] {phone} → код: {code}")
        messages.info(self.request, f"Телефон: {phone} → код: {code}")
        return redirect(f'/verify/?phone={phone}')


class CodeVerifyView(FormView):
    template_name = 'verify.html'
    form_class = CodeForm

    def get_initial(self):
        return {'phone': self.request.GET.get('phone')}

    def form_valid(self, form):

        phone = form.cleaned_data['phone'].replace(" ", "")
        code = form.cleaned_data['code']
        real_code = auth_codes.get(phone)

        print(f"[DEBUG] Input phone: {phone}, Input code: {code}, Real code: {auth_codes.get(phone)}")

        if real_code != code:
            form.add_error('code', 'Неверный код')
            return self.form_invalid(form)

        user, _ = User.objects.get_or_create(phone=phone)
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        auth_codes.pop(phone, None)

        if self.request.user.is_authenticated:
            print("Пользователь аутентифицирован!")

        return redirect('profile')


class ProfileTemplateView(TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({
            'user': user,
            'activated_code': user.used_invite_code,
            'your_code': user.invite_code,
            'invited_users': user.invited_users.all(),
        })
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        code = request.POST.get("invite_code", "").strip()

        if not code:
            context["error"] = "Введите инвайт-код."
            return self.render_to_response(context)

        if request.user.used_invite_code:
            context["error"] = "Инвайт-код уже активирован."
            return self.render_to_response(context)

        try:
            inviter = User.objects.get(invite_code=code)
        except User.DoesNotExist:
            context["error"] = "Инвайт-код не найден."
            return self.render_to_response(context)

        if inviter == request.user:
            context["error"] = "Вы не можете активировать свой собственный инвайт-код."
            return self.render_to_response(context)

        request.user.used_invite_code = code
        request.user.save()
        inviter.invited_users.add(request.user)

        context["success"] = "Инвайт-код успешно активирован."
        return self.render_to_response(context)
