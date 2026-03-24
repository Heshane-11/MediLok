from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import (
    DoctorProfile,
    PatientEducation,
    PatientProfile,
    PatientReport,
    ConsultationRequest
)
from .forms import PatientProfileForm, PatientReportForm

from social_django.models import UserSocialAuth
from twilio.rest import Client
from groq import Groq


# ================= BASIC =================

def index(request):
    return render(request, 'index.html')


def login(request):
    return render(request, 'pages/sign-in.html')


# ================= DOCTOR =================

def doctor_list(request):
    doctors = DoctorProfile.objects.all()
    return render(request, 'doctor/doctor_list.html', {'doctors': doctors})


def doctor_detail(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, pk=doctor_id)

    return JsonResponse({
        'doctor_name': doctor.doctor_name,
        'doctor_phone_number': doctor.doctor_phone_number,
        'doctor_timings': doctor.doctor_timings,
        'doctor_bio': doctor.doctor_bio,
        'doctor_room_id': doctor.doctor_room_id,
    })


# 🔥 VIDEO CALL (FINAL LOGIC)

def video_call_with_doctor(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, pk=doctor_id)

    room_id = request.GET.get('roomID')

    if not room_id:
        return HttpResponse("❌ Invalid room")

    try:
        req = ConsultationRequest.objects.get(id=room_id)

        # 🔥 EXPIRY CHECK (ONLY IF NOT JOINED)
        if req.accepted_at and not req.joined:
            if timezone.now() > req.accepted_at + timedelta(minutes=10):
                return HttpResponse("❌ Session expired (join within 10 min)")

        # ✅ MARK AS JOINED (ONLY FIRST TIME)
        if not req.joined:
            req.joined = True
            req.save()

    except ConsultationRequest.DoesNotExist:
        return HttpResponse("❌ Invalid request")

    return render(request, 'doctor/video_call_with_doctor.html', {
        'doctor': doctor,
        'room_id': room_id
    })


# ================= EDUCATION =================

def educational_content(request):
    topics = PatientEducation.objects.all()

    video_ids = []
    for topic in topics:
        url = topic.url
        video_id = url.split('v=')[1] if 'v=' in url else None
        video_ids.append(video_id)

    return render(request, 'patient/education.html', {
        'educational_topics': topics,
        'video_ids': video_ids
    })


# ================= AI =================

def chat_with_ai(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')
        response = get_ai_response(user_input)

        need_doctor = False
        serious_keywords = [
            'chest pain', 'breathing', 'blood', 'severe',
            'high fever', 'unconscious', 'vomiting', 'infection',
            'pain', 'dizziness'
        ]

        for word in serious_keywords:
            if word in user_input.lower():
                need_doctor = True
                break

        return render(request, 'doctor/ai.html', {
            'user_input': user_input,
            'response': response,
            'need_doctor': need_doctor
        })

    return render(request, 'doctor/ai.html')


def get_ai_response(user_input):
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)

        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful Hindi AI doctor."},
                {"role": "user", "content": user_input}
            ],
            model="llama-3.1-8b-instant"
        )

        return chat.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        return "⚠️ AI temporarily unavailable"


# ================= PATIENT PROFILE =================

def check_patient_profile(request):
    try:
        user_social = UserSocialAuth.objects.filter(user=request.user).first()

        if user_social:
            profile = PatientProfile.objects.filter(user=user_social).first()
            if profile:
                return redirect('doctor_list')

        return redirect('patient_profile')

    except:
        return redirect('login')


def patient_profile(request):
    try:
        user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
        if not user_social_auth:
            return redirect('login')

        profile = PatientProfile.objects.filter(user=user_social_auth).first()

        if request.method == 'POST':
            form = PatientProfileForm(request.POST, instance=profile)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.user = user_social_auth
                profile.save()
                return redirect('doctor_list')
        else:
            form = PatientProfileForm(instance=profile)

        return render(request, 'patient/patient_profile_form.html', {'form': form})

    except Exception as e:
        print(e)
        return redirect('login')


# ================= REQUEST SYSTEM =================

def request_consultation(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, pk=doctor_id)
    user_social = UserSocialAuth.objects.filter(user=request.user).first()

    if request.method == 'POST':
        call_type = request.POST.get('call_type')

        ConsultationRequest.objects.create(
            patient=user_social,
            doctor=doctor,
            call_type=call_type
        )

        return render(request, 'doctor/request_sent.html', {'doctor': doctor})

    return redirect('doctor_list')


# ================= DOCTOR DASHBOARD =================

def doctor_requests(request):
    requests = ConsultationRequest.objects.all().order_by('-created_at')
    return render(request, 'doctor/doctor_requests.html', {'requests': requests})


def accept_request(request, request_id):
    req = get_object_or_404(ConsultationRequest, id=request_id)

    req.status = 'accepted'
    req.accepted_at = timezone.now()
    req.joined = False   # 🔥 RESET
    req.save()

    return redirect('doctor_requests')


def reject_request(request, request_id):
    req = get_object_or_404(ConsultationRequest, id=request_id)
    req.status = 'rejected'
    req.save()

    return redirect('doctor_requests')


# ================= PATIENT LIST =================

def patient_list(request):
    patients = UserSocialAuth.objects.all()
    return render(request, 'patient/patient_list.html', {'patients': patients})


# ================= REPORT =================

def send_report_via_sms(report, patient_name, dr_name):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    body = f"""
Patient: {patient_name}
Doctor: {dr_name}
Disease: {report.disease}
Precaution: {report.precaution}
Medication: {report.medication}
"""

    client.messages.create(
        body=body,
        from_=settings.TWILIO_PHONE_NUMBER,
        to='+91XXXXXXXXXX'
    )


def fill_report(request, patient_id):
    patient = get_object_or_404(UserSocialAuth, pk=patient_id)

    if request.method == 'POST':
        form = PatientReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = patient
            report.save()

            patient_name = f"{patient.user.first_name} {patient.user.last_name}"
            dr_name = report.dr_name.doctor_name

            send_report_via_sms(report, patient_name, dr_name)

            return redirect('doctor_requests')

    else:
        form = PatientReportForm()

    return render(request, 'patient/patient_report.html', {
        'form': form,
        'patient': patient
    })


# ================= PATIENT REQUESTS =================

def my_requests(request):
    try:
        user_social = UserSocialAuth.objects.filter(user=request.user).first()

        if not user_social:
            return redirect('login')

        requests = ConsultationRequest.objects.filter(
            patient=user_social
        ).order_by('-id')

        return render(request, 'patient/my_requests.html', {
            'requests': requests
        })

    except Exception as e:
        print("ERROR:", e)
        return redirect('login')