from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.utils import timezone
from datetime import timedelta

from .models import (
    DoctorProfile,
    PatientEducation,
    PatientProfile,
    PatientReport,
    ConsultationRequest,
    DoctorReview
)
from .forms import PatientProfileForm, PatientReportForm

from social_django.models import UserSocialAuth
from twilio.rest import Client
from groq import Groq
from django.contrib.auth.decorators import login_required

# ================= BASIC =================

def index(request):
    return render(request, 'index.html')



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            return render(request, "pages/sign-in.html", {
                "error": "Invalid username or password"
            })

    return render(request, "pages/sign-in.html")



def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        location = request.POST.get("location")
        age = request.POST.get("age")
        gender = request.POST.get("gender")

        if User.objects.filter(username=username).exists():
            return render(request, "pages/sign-up.html", {
                "error": "Username already exists"
            })
        # ✅ Create Django User
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # ✅ Create dummy social auth (required for your model)
        social = UserSocialAuth.objects.create(
            user=user,
            provider="manual",
            uid=user.username
        )

        # ✅ Create Patient Profile
        PatientProfile.objects.create(
            user=social,
            name=username,
            last_name="",
            age=int(age) if age else 0,
            gender=gender,
            location=location,
            diseases="",
            phone_number=phone_number
        )

        # ✅ Redirect to login
        return redirect('login')

    return render(request, "pages/sign-up.html")



import json
from django.forms.models import model_to_dict

@login_required(login_url='login')
def dashboard(request):
    if hasattr(request.user, 'doctorprofile'):
        return redirect('doctor_dashboard')
    return redirect('patient_dashboard')

@login_required(login_url='login')
def patient_dashboard(request):
    if hasattr(request.user, 'doctorprofile'):
        return redirect('doctor_dashboard')
    
    user_social = UserSocialAuth.objects.filter(user=request.user).first()
    profile = PatientProfile.objects.filter(user=user_social).first()
    
    requests_qs = ConsultationRequest.objects.filter(patient=user_social).order_by('-id')
    requests_data = []
    
    for req in requests_qs:
        req.remaining_seconds = 0
        if req.status == 'accepted' and req.accepted_at:
            diff = (timezone.now() - req.accepted_at).total_seconds()
            if diff > 600:
                req.status = 'rejected'
                req.rejection_reason = "Time expired (Patient did not join within 10 minutes)"
                req.save()
            else:
                req.remaining_seconds = int(600 - diff)
                
        requests_data.append({
            'id': req.id,
            'doctor_name': req.doctor.doctor_name,
            'status': req.status,
            'call_type': req.call_type,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
            'remaining_seconds': req.remaining_seconds,
            'doctor_id': req.doctor.id
        })
        
    dashboard_data = {
        'profile': {
            'name': profile.name if profile else request.user.username,
            'age': profile.age if profile else None,
            'gender': profile.gender if profile else None,
        },
        'requests': requests_data
    }
    
    return render(request, "pages/patient_dashboard.html", {
        'dashboard_data_json': json.dumps(dashboard_data)
    })

@login_required(login_url='doctor_login')
def doctor_dashboard(request):
    if not hasattr(request.user, 'doctorprofile'):
        return redirect('patient_dashboard')
        
    profile = request.user.doctorprofile
    requests_qs = ConsultationRequest.objects.filter(doctor=profile).order_by('-created_at')
    
    pending_requests = []
    active_consultations = []
    completed_consultations = 0 # Dummy for now
    today_consultations = 0
    
    for req in requests_qs:
        # Expiry Check
        if req.status == 'accepted' and req.accepted_at:
            diff = (timezone.now() - req.accepted_at).total_seconds()
            if diff > 600:
                req.status = 'rejected'
                req.rejection_reason = "Time expired (Patient did not join within 10 minutes)"
                req.save()
                
        if req.status == 'pending':
            symptom_summary = f"Patient reported issues: {req.patient.patientprofile.diseases}" if hasattr(req.patient, 'patientprofile') else "No details"
            pending_requests.append({
                'id': req.id,
                'patient_name': req.patient.user.first_name or req.patient.user.username,
                'symptom_summary': symptom_summary,
                'created_at': req.created_at.strftime('%H:%M %p'),
                'call_type': req.call_type
            })
        elif req.status == 'accepted':
            active_consultations.append({
                'id': req.id,
                'patient_name': req.patient.user.first_name or req.patient.user.username,
                'doctor_id': profile.id
            })
            
        if req.created_at.date() == timezone.now().date():
            today_consultations += 1
            
    completed_consultations = ConsultationRequest.objects.filter(doctor=profile, status='completed').count()

    dashboard_data = {
        'profile': {
            'name': profile.doctor_name,
            'specialization': 'General Physician', # Add to model later if needed
            'is_available': profile.is_available
        },
        'stats': {
            'total_patients': UserSocialAuth.objects.count(), # Global for now
            'pending_requests': len(pending_requests),
            'completed_consultations': completed_consultations
        },
        'pending_requests': pending_requests,
        'active_consultations': active_consultations
    }
    
    return render(request, "pages/doctor_dashboard.html", {
        'dashboard_data_json': json.dumps(dashboard_data)
    })

def doctor_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if hasattr(user, 'doctorprofile'):
                auth_login(request, user)
                return redirect('dashboard')
            else:
                return render(request, "pages/doctor-sign-in.html", {
                    "error": "This account is not a doctor account."
                })
        else:
            return render(request, "pages/doctor-sign-in.html", {
                "error": "Invalid username or password"
            })

    return render(request, "pages/doctor-sign-in.html")

def doctor_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        doctor_name = request.POST.get("doctor_name")
        phone_number = request.POST.get("phone_number")
        doctor_bio = request.POST.get("doctor_bio", "")
        
        if User.objects.filter(username=username).exists():
            return render(request, "pages/doctor-sign-up.html", {
                "error": "Username already exists"
            })
            
        user = User.objects.create_user(
            username=username,
            password=password
        )
        
        DoctorProfile.objects.create(
            user=user,
            doctor_name=doctor_name,
            doctor_phone_number=phone_number,
            doctor_bio=doctor_bio,
            doctor_timings=timezone.now()
        )
        
        return redirect('doctor_login')
        
    return render(request, "pages/doctor-sign-up.html")



def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='doctor_login')
def profile(request):
    if not hasattr(request.user, 'doctorprofile'):
        return redirect('patient_dashboard')

    doctor = request.user.doctorprofile
    success = False
    error   = None

    if request.method == 'POST':
        doctor_name        = request.POST.get('doctor_name', '').strip()
        doctor_bio         = request.POST.get('doctor_bio', '').strip()
        doctor_phone       = request.POST.get('doctor_phone_number', '').strip()
        doctor_room_id     = request.POST.get('doctor_room_id', '').strip()

        if not doctor_name:
            error = 'Name is required.'
        else:
            doctor.doctor_name        = doctor_name
            doctor.doctor_bio         = doctor_bio
            doctor.doctor_phone_number = doctor_phone
            doctor.doctor_room_id     = doctor_room_id
            if request.FILES.get('doctor_image'):
                doctor.doctor_image = request.FILES['doctor_image']
            doctor.save()
            success = True

    return render(request, 'doctor/doctor_profile_edit.html', {
        'doctor':  doctor,
        'success': success,
        'error':   error,
    })
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
def video_call_with_doctor(request, request_id):
    req = get_object_or_404(ConsultationRequest, id=request_id)
    doctor = req.doctor

    # 🔥 EXPIRY CHECK — 10 min join window only (not a call time limit)
    if req.accepted_at and not req.joined:
        if timezone.now() > req.accepted_at + timedelta(minutes=10):
            req.status = 'rejected'
            req.rejection_reason = "Time expired (Patient did not join within 10 minutes)"
            req.save()
            return HttpResponse("❌ Session expired. The doctor's request has closed. Please book a new consultation.")

    # ✅ MARK AS JOINED (ONLY FIRST TIME)
    if not req.joined:
        req.joined = True
        req.save()

    is_patient = (request.user == req.patient.user)

    return render(request, 'doctor/video_call_with_doctor.html', {
        'doctor': doctor,
        'zego_room_id': str(req.id),
        'is_patient': is_patient,
        'req_id': req.id
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


@login_required(login_url='login')
def consultation_feedback(request, request_id):
    req = get_object_or_404(ConsultationRequest, id=request_id)
    
    # Security check: Ensure this is the patient of the consultation
    user_social = UserSocialAuth.objects.filter(user=request.user).first()
    if not user_social or req.patient != user_social:
        return redirect('patient_dashboard')
        
    # Ensure call was accepted
    if req.status not in ['accepted', 'completed']:
        return redirect('patient_dashboard')
        
    if request.method == 'POST':
        try:
            rating_overall = int(request.POST.get('rating_overall', 5))
            rating_listening = int(request.POST.get('rating_listening', 5))
            rating_guidance = int(request.POST.get('rating_guidance', 5))
            rating_clarity = int(request.POST.get('rating_clarity', 5))
            rating_recommend = int(request.POST.get('rating_recommend', 5))
            comments = request.POST.get('comments', '').strip()
            
            # Save review
            DoctorReview.objects.update_or_create(
                request=req,
                defaults={
                    'rating_overall': rating_overall,
                    'rating_listening': rating_listening,
                    'rating_guidance': rating_guidance,
                    'rating_clarity': rating_clarity,
                    'rating_recommend': rating_recommend,
                    'comments': comments
                }
            )
            
            # Mark consultation request status as completed
            req.status = 'completed'
            req.save()
            
            return redirect('/patient-dashboard/?feedback_submitted=true')
        except Exception as e:
            return render(request, 'patient/consultation_feedback.html', {
                'req': req,
                'error': f'Invalid input: {e}'
            })
            
    return render(request, 'patient/consultation_feedback.html', {'req': req})


# ================= DOCTOR DASHBOARD =================

@login_required(login_url='doctor_login')
def doctor_requests(request):
    if not hasattr(request.user, 'doctorprofile'):
        return redirect('dashboard')
        
    requests = ConsultationRequest.objects.all().order_by('-created_at')
    
    # ✅ Expiry Check & Remaining Time Calculation
    for req in requests:
        req.remaining_seconds = 0
        if req.status == 'accepted' and req.accepted_at:
            diff = (timezone.now() - req.accepted_at).total_seconds()
            if diff > 600:
                req.status = 'rejected'
                req.rejection_reason = "Time expired (Patient did not join within 10 minutes)"
                req.save()
            else:
                req.remaining_seconds = int(600 - diff)
                
    return render(request, 'doctor/doctor_requests.html', {'requests': requests})


from django.urls import reverse

def accept_request(request, request_id):
    req = get_object_or_404(ConsultationRequest, id=request_id)

    req.status = 'accepted'
    req.accepted_at = timezone.now()
    req.joined = False
    req.save()

    url = reverse('video_call_with_doctor', args=[req.id])
    return redirect(url)


def reject_request(request, request_id):
    req = get_object_or_404(ConsultationRequest, id=request_id)
    req.status = 'rejected'
    req.save()

    return redirect('doctor_requests')

# ================= API ENDPOINTS =================

@login_required
def toggle_availability(request):
    if request.method == 'POST' and hasattr(request.user, 'doctorprofile'):
        profile = request.user.doctorprofile
        profile.is_available = not profile.is_available
        profile.save()
        return JsonResponse({'success': True, 'message': 'Availability updated', 'data': {'is_available': profile.is_available}})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def api_accept_request(request, request_id):
    if request.method == 'POST' and hasattr(request.user, 'doctorprofile'):
        req = get_object_or_404(ConsultationRequest, id=request_id, doctor=request.user.doctorprofile)
        req.status = 'accepted'
        req.accepted_at = timezone.now()
        req.joined = False
        req.save()
        return JsonResponse({'success': True, 'message': 'Request accepted', 'data': {'id': req.id}})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def api_reject_request(request, request_id):
    if request.method == 'POST' and hasattr(request.user, 'doctorprofile'):
        req = get_object_or_404(ConsultationRequest, id=request_id, doctor=request.user.doctorprofile)
        req.status = 'rejected'
        req.save()
        return JsonResponse({'success': True, 'message': 'Request rejected', 'data': {'id': req.id}})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)



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

    patient_phone = '+91XXXXXXXXXX'
    try:
        profile = report.user.patientprofile
        if profile and profile.phone_number:
            patient_phone = profile.phone_number
            if not patient_phone.startswith('+'):
                if len(patient_phone) == 10:
                    patient_phone = '+91' + patient_phone
    except Exception as e:
        print("Error reading patient phone number for SMS:", e)

    try:
        client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=patient_phone
        )
    except Exception as e:
        print("Twilio SMS transmission failed:", e)


@login_required(login_url='doctor_login')
def fill_report(request, patient_id):
    patient = get_object_or_404(UserSocialAuth, pk=patient_id)
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)

    if request.method == 'POST':
        form = PatientReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = patient
            report.dr_name = doctor_profile
            report.save()

            patient_name = f"{patient.user.first_name} {patient.user.last_name}".strip() or patient.user.username
            dr_name = doctor_profile.doctor_name

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

        # ✅ Expiry Check & Remaining Time Calculation
        for req in requests:
            req.remaining_seconds = 0
            if req.status == 'accepted' and req.accepted_at:
                diff = (timezone.now() - req.accepted_at).total_seconds()
                if diff > 600:
                    req.status = 'rejected'
                    req.rejection_reason = "Time expired (Patient did not join within 10 minutes)"
                    req.save()
                else:
                    req.remaining_seconds = int(600 - diff)

        return render(request, 'patient/my_requests.html', {
            'requests': requests
        })

    except Exception as e:
        print("ERROR:", e)
        return redirect('login')