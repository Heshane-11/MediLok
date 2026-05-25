from django.shortcuts import render, HttpResponse, redirect
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
import os
import pickle

# Heavy ML imports are loaded lazily on first use to avoid slow server startup
_ml_loaded = False
np = None
cv2 = None
imutils = None
joblib = None
load_model = None
preprocess_input = None

def _load_ml_libs():
    global _ml_loaded, np, cv2, imutils, joblib, load_model, preprocess_input
    if not _ml_loaded:
        import numpy as _np
        import cv2 as _cv2
        import imutils as _imutils
        import joblib as _joblib
        from keras.models import load_model as _load_model
        from keras.applications.vgg16 import preprocess_input as _preprocess_input
        np = _np
        cv2 = _cv2
        imutils = _imutils
        joblib = _joblib
        load_model = _load_model
        preprocess_input = _preprocess_input
        _ml_loaded = True




############################################# BRAIN TUMOR FUNCTIONS ################################################

def preprocess_imgs(set_name, img_size):
    """
    Resize and apply VGG-15 preprocessing
    """
    _load_ml_libs()
    set_new = []
    for img in set_name:
        img = cv2.resize(img,dsize=img_size,interpolation=cv2.INTER_CUBIC)
        set_new.append(preprocess_input(img))
    return np.array(set_new)

def crop_imgs(set_name, add_pixels_value=0):
    """
    Finds the extreme points on the image and crops the rectangular out of them
    """
    _load_ml_libs()
    set_new = []
    for img in set_name:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # threshold the image, then perform a series of erosions +
        # dilations to remove any small regions of noise
        thresh = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)

        # find contours in thresholded image, then grab the largest one
        cnts = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        c = max(cnts, key=cv2.contourArea)

        # find the extreme points
        extLeft = tuple(c[c[:, :, 0].argmin()][0])
        extRight = tuple(c[c[:, :, 0].argmax()][0])
        extTop = tuple(c[c[:, :, 1].argmin()][0])
        extBot = tuple(c[c[:, :, 1].argmax()][0])

        ADD_PIXELS = add_pixels_value
        new_img = img[extTop[1]-ADD_PIXELS:extBot[1]+ADD_PIXELS,
                      extLeft[0]-ADD_PIXELS:extRight[0]+ADD_PIXELS].copy()
        set_new.append(new_img)

    return np.array(set_new)


# Lazy loading models
_models = {}

def get_model(name, loader_type='keras'):
    _load_ml_libs()
    if name not in _models:
        print(f"Loading model: {name}...")
        if loader_type == 'keras':
            _models[name] = load_model(f'models/{name}')
        elif loader_type == 'pickle':
            _models[name] = pickle.load(open(f'models/{name}', 'rb'))
        elif loader_type == 'joblib':
            _models[name] = joblib.load(f'models/{name}')
    return _models[name]

def diseases(request):
    return render(request, 'disease/homepage.html')

def covid(request):
    return render(request, 'disease/covid.html')

def braintumour(request):
    return render(request, 'disease/braintumor.html')

def breastcancer(request):
    return render(request, 'disease/breastcancer.html')

def diabetes(request):
    return render(request, 'disease/diabetes.html')

def heartdisease(request):
    return render(request, 'disease/heartdisease.html')

def pneumonia(request):
    return render(request, 'disease/pneumonia.html')

def alzheimer(request):
    return render(request, 'disease/alzheimer.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in settings.ALLOWED_EXTENSIONS







def resultc(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        file = request.FILES['file']

        if file and allowed_file(file.name):
            _load_ml_libs()
            # filename = secure_filename(file.filename)
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            filename = fs.save(file.name, file)
            messages.success(request,'Image successfully uploaded and displayed below')
            img = cv2.imread('media/'+filename)
            img = cv2.resize(img, (224, 224))
            img = img.reshape(1, 224, 224, 3)
            img = img/255.0
            model = get_model('covid.h5')
            pred = model.predict(img)
            if pred < 0.5:
                pred = 0
            else:
                pred = 1

            context = {
                'filename': filename,
                'fn': firstname,
                'ln': lastname,
                'age': age,
                'r': pred,
                'gender': gender,
            }
            # pb.push_sms(pb.devices[0],str(phone), 'Hello {},\nYour COVID-19 test results are ready.\nRESULT: {}'.format(firstname,['POSITIVE','NEGATIVE'][pred]))
            return render(request,'disease/resultc.html', context)

        else:
            messages.error(request,'Allowed image types are - png, jpg, jpeg')
            return redirect(request.url)
        


    
def resultbc(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        
        try:
            cpm = float(request.POST.get('concave_points_mean', 0))
            am = float(request.POST.get('area_mean', 0))
            rm = float(request.POST.get('radius_mean', 0))
            pm = float(request.POST.get('perimeter_mean', 0))
            cm = float(request.POST.get('concavity_mean', 0))
        except (ValueError, TypeError):
            cpm = am = rm = pm = cm = 0.0

        model = get_model('cancer_model.pkl', 'joblib')
        pred = model.predict(np.array([cpm, am, rm, pm, cm]).reshape(1, -1))
        
        result_val = int(pred[0])

        context = {
            'fn': firstname,
            'ln': lastname,
            'age': age,
            'r': result_val,
            'gender': gender,
        }

        if phone:
            try:
                from twilio.rest import Client
                from django.conf import settings
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                body = f"Hello {firstname},\nYour MediLok test results for Breast Cancer are ready.\nRESULT: {['NEGATIVE','POSITIVE'][result_val]}"
                client.messages.create(
                    body=body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
            except Exception as e:
                print("Error sending breast cancer prediction SMS:", e)

        return render(request, 'disease/resultbc.html', context)


def resulta(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        file = request.FILES['file']

        if file and allowed_file(file.name):
            # filename = secure_filename(file.filename)
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            filename = fs.save(file.name, file)
            messages.success(request,'Image successfully uploaded and displayed below')
            img = cv2.imread('media/'+filename)
            img = cv2.resize(img, (176, 176))
            img = img.reshape(1, 176, 176, 3)
            img = img/255.0
            model = get_model('alzheimer_model.h5')
            pred = model.predict(img)
            pred = pred[0].argmax()
            print(pred)
            context = {
                'filename': filename,
                'fn': firstname,
                'ln': lastname,
                'age': age,
                'r': pred,
                'gender': gender,
            }
            # pb.push_sms(pb.devices[0],str(phone), 'Hello {},\nYour Alzheimer test results are ready.\nRESULT: {}'.format(firstname,['NonDemented','VeryMildDemented','MildDemented','ModerateDemented'][pred]))
            return render(request,'disease/resulta.html', context)

        else:
            messages.error(request,'Allowed image types are - png, jpg, jpeg')
            return redirect(request.url)
        

def resultp(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        file = request.FILES['file']

        if file and allowed_file(file.name):
            # filename = secure_filename(file.filename)
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            filename = fs.save(file.name, file)
            messages.success(request,'Image successfully uploaded and displayed below')
            img = cv2.imread('media/'+filename)
            img = cv2.resize(img, (150, 150))
            img = img.reshape(1, 150, 150, 3)
            img = img/255.0
            model = get_model('pneumonia_model.h5')
            pred = model.predict(img)
            if pred < 0.5:
                pred = 0
            else:
                pred = 1

            context = {
                'filename': filename,
                'fn': firstname,
                'ln': lastname,
                'age': age,
                'r': pred,
                'gender': gender,
            }
            # pb.push_sms(pb.devices[0],str(phone), 'Hello {},\nYour COVID-19 test results are ready.\nRESULT: {}'.format(firstname,['POSITIVE','NEGATIVE'][pred]))
            return render(request,'disease/resultp.html', context)

        else:
            messages.error(request,'Allowed image types are - png, jpg, jpeg')
            return redirect(request.url)
        

def resulth(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        nmv = float(request.POST.get('nmv'))
        tcp = float(request.POST.get('tcp'))
        eia = float(request.POST.get('eia'))
        thal = float(request.POST.get('thal'))
        op = float(request.POST.get('op'))
        mhra = float(request.POST.get('mhra'))
        age = float(request.POST.get('age'))
        print(np.array([nmv, tcp, eia, thal, op, mhra, age]).reshape(1, -1))
        model = get_model('heart_disease.pickle.dat', 'pickle')
        pred = model.predict(
            np.array([nmv, tcp, eia, thal, op, mhra, age]).reshape(1, -1))
        
        context = {
                'fn': firstname,
                'ln': lastname,
                'age': age,
                'r': pred,
                'gender': gender,
            }
        # pb.push_sms(pb.devices[0],str(phone), 'Hello {},\nYour Diabetes test results are ready.\nRESULT: {}'.format(firstname,['NEGATIVE','POSITIVE'][pred]))
        return render(request,'disease/resulth.html', context)
    
def resultd(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        
        try:
            pregnancies = float(request.POST.get('pregnancies', 0))
            glucose = float(request.POST.get('glucose', 0))
            bloodpressure = float(request.POST.get('bloodpressure', 0))
            insulin = float(request.POST.get('insulin', 0))
            bmi = float(request.POST.get('bmi', 0))
            diabetespedigree = float(request.POST.get('diabetespedigree', 0))
            age = float(request.POST.get('age', 0))
            skinthickness = float(request.POST.get('skin', 0))
        except (ValueError, TypeError):
            pregnancies = glucose = bloodpressure = insulin = bmi = diabetespedigree = age = skinthickness = 0.0

        model = get_model('diabetes.sav', 'pickle')
        pred = model.predict(
            [[pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, diabetespedigree, age]])
        
        result_val = int(pred[0])

        context = {
            'fn': firstname,
            'ln': lastname,
            'age': age,
            'r': result_val,
            'gender': gender,
        }
        
        if phone:
            try:
                from twilio.rest import Client
                from django.conf import settings
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                body = f"Hello {firstname},\nYour MediLok test results for Diabetes are ready.\nRESULT: {['NEGATIVE','POSITIVE'][result_val]}"
                client.messages.create(
                    body=body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
            except Exception as e:
                print("Error sending diabetes prediction SMS:", e)

        return render(request, 'disease/resultd.html', context)


def resultbt(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        file = request.FILES['file']

        if file and allowed_file(file.name):
            # filename = secure_filename(file.filename)
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            filename = fs.save(file.name, file)
            messages.success(request,'Image successfully uploaded and displayed below')
            img = cv2.imread('media/'+filename)
            img = crop_imgs([img])
            img = img.reshape(img.shape[1:])
            img = preprocess_imgs([img], (224, 224))
            model = get_model('braintumor.h5')
            pred = model.predict(img)
            if pred < 0.5:
                pred = 0
            else:
                pred = 1

            context = {
                'filename': filename,
                'fn': firstname,
                'ln': lastname,
                'age': age,
                'r': pred,
                'gender': gender,
            }
            # pb.push_sms(pb.devices[0],str(phone), 'Hello {},\nYour Brain Tumor test results are ready.\nRESULT: {}'.format(firstname,['NEGATIVE','POSITIVE'][pred]))
            return render(request,'disease/resultbt.html', context)

        else:
            messages.error(request,'Allowed image types are - png, jpg, jpeg')
            return redirect(request.url)

