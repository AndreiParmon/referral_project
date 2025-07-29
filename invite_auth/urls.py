from django.urls import path

from invite_auth.views import PhoneLoginView, CodeVerifyView, ProfileTemplateView
from invite_auth.views import (
    RequestCodeView, VerifyCodeView, ProfileView, ActivateInviteCodeView
)

urlpatterns = [
    path('api/request-code/', RequestCodeView.as_view(), name='api-request-code'),
    path('api/verify-code/', VerifyCodeView.as_view(), name='api-verify-code'),
    path('api/profile/', ProfileView.as_view(), name='api-profile'),
    path('api/activate-invite/', ActivateInviteCodeView.as_view(), name='api-activate-invite'),

    path('', PhoneLoginView.as_view(), name='login'),
    path('verify/', CodeVerifyView.as_view(), name='verify'),
    path('profile/', ProfileTemplateView.as_view(), name='profile'),

]
