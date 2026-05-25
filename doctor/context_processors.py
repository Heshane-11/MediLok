def user_role_processor(request):
    if request.user.is_authenticated:
        is_doctor = hasattr(request.user, 'doctorprofile')
        is_patient = hasattr(request.user, 'usersocialauth')
        return {
            'is_doctor': is_doctor,
            'is_patient': is_patient
        }
    return {
        'is_doctor': False,
        'is_patient': False
    }
