from django.db import models
from social_django.models import UserSocialAuth


# =========================
# DOCTOR PROFILE
# =========================
class DoctorProfile(models.Model):
    doctor_name = models.CharField(max_length=100, null=True, blank=True)
    doctor_image = models.ImageField(upload_to='doctor_images/')
    doctor_timings = models.DateTimeField()
    doctor_bio = models.CharField(max_length=255)
    doctor_room_id = models.CharField(max_length=20, null=True, blank=True)
    doctor_phone_number = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.doctor_name or "Doctor"


# =========================
# PATIENT EDUCATION
# =========================
class PatientEducation(models.Model):
    topic = models.CharField(max_length=50)
    url = models.URLField(max_length=200)

    def __str__(self):
        return f'{self.topic} - {self.url}'


# =========================
# PATIENT PROFILE
# =========================
class PatientProfile(models.Model):
    user = models.OneToOneField(UserSocialAuth, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    location = models.CharField(max_length=100)
    diseases = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.name} {self.last_name}'


# =========================
# PATIENT REPORT
# =========================
class PatientReport(models.Model):
    user = models.ForeignKey(UserSocialAuth, on_delete=models.CASCADE)
    dr_name = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    disease = models.CharField(max_length=200)
    precaution = models.TextField()
    medication = models.TextField()

    def __str__(self):
        return f'{self.user.user.first_name} {self.user.user.last_name} - {self.disease}'


# =========================
# CONSULTATION REQUEST
# =========================
class ConsultationRequest(models.Model):
    patient = models.ForeignKey(UserSocialAuth, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    CALL_TYPE = (
        ('voice', 'Voice'),
        ('video', 'Video'),
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    call_type = models.CharField(max_length=10, choices=CALL_TYPE)

    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ NEW FIELD (IMPORTANT 🔥)
    accepted_at = models.DateTimeField(null=True, blank=True)
    joined = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.patient.user.first_name} → {self.doctor.doctor_name} ({self.status})"