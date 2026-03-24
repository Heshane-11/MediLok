from django.contrib import admin
from django.urls import path, include
from .views import (
    reject_request, accept_request, doctor_requests,
    login, doctor_list, doctor_detail, video_call_with_doctor,
    chat_with_ai, educational_content, patient_profile,
    check_patient_profile, request_consultation,
    patient_list, fill_report, index, my_requests
)

urlpatterns = [
    path('', index, name='index'),
    path('login', login, name='login'),

    path('doctor_list', doctor_list, name='doctor_list'),
    path('doctor/<int:doctor_id>/', doctor_detail, name='doctor_detail'),

    path('request/<int:doctor_id>/', request_consultation, name='request_consultation'),

    path('doctor_requests/', doctor_requests, name='doctor_requests'),
    path('accept/<int:request_id>/', accept_request, name='accept_request'),
    path('reject/<int:request_id>/', reject_request, name='reject_request'),

    path('video_call/<int:doctor_id>/', video_call_with_doctor, name='video_call_with_doctor'),  # ✅ FIXED

    path('chat_with_ai', chat_with_ai, name='chat_with_ai'),
    path('education', educational_content, name='educational_content'),

    path('patient_profile', patient_profile, name='patient_profile'),
    path('check_patient_profile', check_patient_profile, name='check_patient_profile'),

    path('patient_list/', patient_list, name='patient_list'),
    path('fill_report/<int:patient_id>/', fill_report, name='fill_report'),

    path('my_requests/', my_requests, name='my_requests'),  # ✅ ADD THIS
]