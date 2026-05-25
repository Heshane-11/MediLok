from django.urls import path
from .views import (
    reject_request, accept_request, doctor_requests,
    login_view, doctor_list, doctor_detail, video_call_with_doctor,
    chat_with_ai, educational_content, patient_profile,
    check_patient_profile, request_consultation,
    patient_list, fill_report, index, my_requests,
    signup, dashboard, profile, logout_view,
    doctor_login_view, doctor_signup, patient_dashboard, doctor_dashboard,
    toggle_availability, api_accept_request, api_reject_request,
    consultation_feedback
)

urlpatterns = [
    path('', index, name='index'),
    path('request/<int:request_id>/feedback/', consultation_feedback, name='consultation_feedback'),

    path('login', login_view, name='login'),
    path('signup', signup, name='signup'),
    path('doctor_login', doctor_login_view, name='doctor_login'),
    path('doctor_signup', doctor_signup, name='doctor_signup'),
    path('dashboard', dashboard, name='dashboard'),
    path('patient-dashboard/', patient_dashboard, name='patient_dashboard'),
    path('doctor-dashboard/', doctor_dashboard, name='doctor_dashboard'),
    path('profile', profile, name='profile'),
    path('logout', logout_view, name='logout'),
    path('doctor_list', doctor_list, name='doctor_list'),
    path('doctor/<int:doctor_id>/', doctor_detail, name='doctor_detail'),

    path('request/<int:doctor_id>/', request_consultation, name='request_consultation'),

    path('doctor_requests/', doctor_requests, name='doctor_requests'),
    path('accept/<int:request_id>/', accept_request, name='accept_request'),
    path('reject/<int:request_id>/', reject_request, name='reject_request'),
    path('api/toggle-availability/', toggle_availability, name='toggle_availability'),
    path('api/request/<int:request_id>/accept/', api_accept_request, name='api_accept_request'),
    path('api/request/<int:request_id>/reject/', api_reject_request, name='api_reject_request'),

    path('video_call/<int:request_id>/', video_call_with_doctor, name='video_call_with_doctor'),

    path('chat_with_ai', chat_with_ai, name='chat_with_ai'),
    path('education', educational_content, name='educational_content'),

    path('patient_profile', patient_profile, name='patient_profile'),
    path('check_patient_profile', check_patient_profile, name='check_patient_profile'),

    path('patient_list/', patient_list, name='patient_list'),
    path('fill_report/<int:patient_id>/', fill_report, name='fill_report'),

    path('my_requests/', my_requests, name='my_requests'),
]