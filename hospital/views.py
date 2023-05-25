from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.core.mail import send_mail, EmailMessage, message
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.conf import settings

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/index.html')

def services_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/services.html')

def admin_signup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()
            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)
            return HttpResponseRedirect('adminlogin')
    return render(request,'hospital/adminsignup.html',{'form':form})

def doctor_signup_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST,request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor=doctor.save()
            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)
        return HttpResponseRedirect('doctorlogin')
    return render(request,'hospital/doctorsignup.html',context=mydict)


def patient_signup_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.user=user
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient=patient.save()
            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)
        return HttpResponseRedirect('patientlogin')
    return render(request,'hospital/patientsignup.html',context=mydict)

def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()
def is_doctor(user):
    return user.groups.filter(name='DOCTOR').exists()
def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()

def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_doctor(request.user):
        accountapproval=models.Doctor.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('doctor-dashboard')
        else:
            return render(request,'hospital/doctor_wait_for_approval.html')
    elif is_patient(request.user):
        accountapproval=models.Patient.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('patient-dashboard')
        else:
            return render(request,'hospital/patient_wait_for_approval.html')


# For Admin Related Views

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):

    doctors=models.Doctor.objects.all().order_by('-id')
    patients=models.Patient.objects.all().order_by('-id')

    doctorcount=models.Doctor.objects.all().filter(status=True).count()
    pendingdoctorcount=models.Doctor.objects.all().filter(status=False).count()

    patientcount=models.Patient.objects.all().filter(status=True).count()
    pendingpatientcount=models.Patient.objects.all().filter(status=False).count()

    appointmentcount=models.Appointment.objects.all().filter(status=True).count()
    pendingappointmentcount=models.Appointment.objects.all().filter(status=False).count()
    mydict={
    'doctors':doctors,
    'patients':patients,
    'doctorcount':doctorcount,
    'pendingdoctorcount':pendingdoctorcount,
    'patientcount':patientcount,
    'pendingpatientcount':pendingpatientcount,
    'appointmentcount':appointmentcount,
    'pendingappointmentcount':pendingappointmentcount,
    }
    return render(request,'hospital/admin_dashboard.html',context=mydict)


# this view for sidebar click on admin page
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_view(request):
    return render(request,'hospital/admin_doctor.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_doctor_from_hospital_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-view-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)

    userForm=forms.DoctorUserForm(instance=user)
    doctorForm=forms.DoctorForm(request.FILES,instance=doctor)
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST,instance=user)
        doctorForm=forms.DoctorForm(request.POST,request.FILES,instance=doctor)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.status=True
            doctor.save()
            return redirect('admin-view-doctor')
    return render(request,'hospital/admin_update_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor.status=True
            doctor.save()

            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-doctor')
    return render(request,'hospital/admin_add_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_doctor_view(request):
    #those whose approval are needed
    doctors=models.Doctor.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_doctor.html',{'doctors':doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    doctor.status=True
    doctor.save()
    return redirect(reverse('admin-approve-doctor'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-approve-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor_specialisation.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    return render(request,'hospital/admin_patient.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_patient_from_hospital_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-view-patient')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)

    userForm=forms.PatientUserForm(instance=user)
    patientForm=forms.PatientForm(request.FILES,instance=patient)
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST,instance=user)
        patientForm=forms.PatientForm(request.POST,request.FILES,instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()
            return redirect('admin-view-patient')
    return render(request,'hospital/admin_update_patient.html',context=mydict)





@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            patient=patientForm.save(commit=False)
            patient.user=user
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()

            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-patient')
    return render(request,'hospital/admin_add_patient.html',context=mydict)



#------------------FOR APPROVING PATIENT BY ADMIN----------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    #those whose approval are needed
    patients=models.Patient.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    patient.status=True
    patient.save()
    return redirect(reverse('admin-approve-patient'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-approve-patient')



#--------------------- FOR DISCHARGING PATIENT BY ADMIN START-------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_discharge_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def discharge_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    days=(date.today()-patient.admitDate)
    assignedDoctor=models.User.objects.all().filter(id=patient.assignedDoctorId)
    d=days.days 
    patientDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'day':d,
        'assignedDoctorName':assignedDoctor[0].first_name,
    }
    if request.method == 'POST':
        feeDict ={
            'roomCharge':int(request.POST['roomCharge'])*int(d),
            'doctorFee':request.POST['doctorFee'],
            'medicineCost' : request.POST['medicineCost'],
            'OtherCharge' : request.POST['OtherCharge'],
            'total':(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        }
        patientDict.update(feeDict)
        #for updating to database patientDischargeDetails (pDD)
        pDD=models.PatientDischargeDetails()
        pDD.patientId=pk
        pDD.patientName=patient.get_name
        pDD.assignedDoctorName=assignedDoctor[0].first_name
        pDD.address=patient.address
        pDD.mobile=patient.mobile
        pDD.symptoms=patient.symptoms
        pDD.admitDate=patient.admitDate
        pDD.releaseDate=date.today()
        pDD.daySpent=int(d)
        pDD.medicineCost=int(request.POST['medicineCost'])
        pDD.roomCharge=int(request.POST['roomCharge'])*int(d)
        pDD.doctorFee=int(request.POST['doctorFee'])
        pDD.OtherCharge=int(request.POST['OtherCharge'])
        pDD.total=(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        pDD.save()
        return render(request,'hospital/patient_final_bill.html',context=patientDict)
    return render(request,'hospital/patient_generate_bill.html',context=patientDict)



#--------------for discharge patient bill (pdf) download and printing
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return



def download_pdf_view(request,pk):
    dischargeDetails=models.PatientDischargeDetails.objects.all().filter(patientId=pk).order_by('-id')[:1]
    dict={
        'patientName':dischargeDetails[0].patientName,
        'assignedDoctorName':dischargeDetails[0].assignedDoctorName,
        'address':dischargeDetails[0].address,
        'mobile':dischargeDetails[0].mobile,
        'symptoms':dischargeDetails[0].symptoms,
        'admitDate':dischargeDetails[0].admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
    }
    return render_to_pdf('hospital/download_bill.html',dict)



#-----------------APPOINTMENT START--------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    return render(request,'hospital/admin_appointment.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    appointments=models.Appointment.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    appointmentForm=forms.AppointmentForm()
    mydict={'appointmentForm':appointmentForm,}
    if request.method=='POST':
        appointmentForm=forms.AppointmentForm(request.POST)
        if appointmentForm.is_valid():
            appointment=appointmentForm.save(commit=False)
            appointment.doctorId=request.POST.get('doctorId')
            appointment.patientId=request.POST.get('patientId')
            appointment.doctorName=models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName=models.User.objects.get(id=request.POST.get('patientId')).first_name
            appointment.status=True
            appointment.save()
        return HttpResponseRedirect('admin-view-appointment')
    return render(request,'hospital/admin_add_appointment.html',context=mydict)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    #those whose approval are needed
    appointments=models.Appointment.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.status=True
    appointment.save()
    return redirect(reverse('admin-approve-appointment'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    return redirect('admin-approve-appointment')

#------------------------ DOCTOR RELATED VIEWS START ------------------------------
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    patientcount=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).count()
    appointmentcount=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).count()
    patientdischarged=models.PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=request.user.first_name).count()
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).order_by('-id')
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid).order_by('-id')
    appointments=zip(appointments,patients)
    mydict={
    'patientcount':patientcount,
    'appointmentcount':appointmentcount,
    'patientdischarged':patientdischarged,
    'appointments':appointments,
    'doctor':models.Doctor.objects.get(user_id=request.user.id),
    }
    return render(request,'hospital/doctor_dashboard.html',context=mydict)



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    mydict={
    'doctor':models.Doctor.objects.get(user_id=request.user.id), 
    }
    return render(request,'hospital/doctor_patient.html',context=mydict)



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_discharge_patient_view(request):
    dischargedpatients=models.PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=request.user.first_name)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_discharge_patient.html',{'dischargedpatients':dischargedpatients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_appointment.html',{'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_view_appointment.html',{'appointments':appointments,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})

#------------------------ PATIENT RELATED VIEWS START ------------------------------

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id)
    doctor=models.Doctor.objects.get(user_id=patient.assignedDoctorId)
    mydict={
    'patient':patient,
    'doctorName':doctor.get_name,
    'doctorMobile':doctor.mobile,
    'doctorAddress':doctor.address,
    'symptoms':patient.symptoms,
    'doctorDepartment':doctor.department,
    'admitDate':patient.admitDate,
    }
    return render(request,'hospital/patient_dashboard.html',context=mydict)



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_appointment.html',{'patient':patient})



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_book_appointment_view(request):
    appointmentForm=forms.PatientAppointmentForm()
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    message=None
    mydict={'appointmentForm':appointmentForm,'patient':patient,'message':message}
    if request.method=='POST':
        appointmentForm=forms.PatientAppointmentForm(request.POST)
        if appointmentForm.is_valid():
            print(request.POST.get('doctorId'))
            desc=request.POST.get('description')
            doctor=models.Doctor.objects.get(user_id=request.POST.get('doctorId'))
            appointment=appointmentForm.save(commit=False)
            appointment.doctorId=request.POST.get('doctorId')
            appointment.patientId=request.user.id #----user can choose any patient but only their info will be stored
            appointment.doctorName=models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName=request.user.first_name #----user can choose any patient but only their info will be stored
            appointment.status=False
            appointment.save()
        return HttpResponseRedirect('patient-view-appointment')
    return render(request,'hospital/patient_book_appointment.html',context=mydict)





@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    appointments=models.Appointment.objects.all().filter(patientId=request.user.id)
    return render(request,'hospital/patient_view_appointment.html',{'appointments':appointments,'patient':patient})



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_discharge_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    dischargeDetails=models.PatientDischargeDetails.objects.all().filter(patientId=patient.id).order_by('-id')[:1]
    patientDict=None
    if dischargeDetails:
        patientDict ={
        'is_discharged':True,
        'patient':patient,
        'patientId':patient.id,
        'patientName':patient.get_name,
        'assignedDoctorName':dischargeDetails[0].assignedDoctorName,
        'address':patient.address,
        'mobile':patient.mobile,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
        }
        print(patientDict)
    else:
        patientDict={
            'is_discharged':False,
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_discharge.html',context=patientDict)

from joblib import load
model_breast = load('./savedmodel/breast_model.joblib')
model_heart = load('./savedmodel/heart_model.joblib')
model_stroke = load('./savedmodel/stroke_model.joblib')
model_fetal = load('./savedmodel/fetal_model.joblib')
model_lung = load('./savedmodel/lung_model.joblib')
model_diabetes = load('./savedmodel/diabetes_model.joblib')
model_depression = load('./savedmodel/depression_model.joblib')

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def breast_cancer_prediction(request):
    if request.method == 'POST':
        mean_radius = float(request.POST['mean_radius'])
        mean_texture = float(request.POST['mean_texture'])
        mean_perimeter = float(request.POST['mean_perimeter'])
        mean_area = float(request.POST['mean_area'])
        mean_smoothness = float(request.POST['mean_smoothness'])
        mean_compactness = float(request.POST['mean_compactness'])
        mean_concavity = float(request.POST['mean_concavity'])
        mean_concave_points = float(request.POST['mean_concave_points'])
        mean_symmetry = float(request.POST['mean_symmetry'])
        mean_fractal_dimension = float(request.POST['mean_fractal_dimension'])
        radius_error = float(request.POST['radius_error'])
        texture_error = float(request.POST['texture_error'])
        perimeter_error = float(request.POST['perimeter_error'])
        area_error = float(request.POST['area_error'])
        smoothness_error = float(request.POST['smoothness_error'])
        compactness_error = float(request.POST['compactness_error'])
        concavity_error = float(request.POST['concavity_error'])
        concave_points_error = float(request.POST['concave_points_error'])
        symmetry_error = float(request.POST['symmetry_error'])
        fractal_dimension_error = float(request.POST['fractal_dimension_error'])
        worst_radius = float(request.POST['worst_radius'])
        worst_texture = float(request.POST['worst_texture'])
        worst_perimeter = float(request.POST['worst_perimeter'])
        worst_area = float(request.POST['worst_area'])
        worst_smoothness = float(request.POST['worst_smoothness'])
        worst_compactness = float(request.POST['worst_compactness'])
        worst_concavity = float(request.POST['worst_concavity'])
        worst_concave_points = float(request.POST['worst_concave_points'])
        worst_symmetry = float(request.POST['worst_symmetry'])
        worst_fractal_dimension = float(request.POST['worst_fractal_dimension'])
        y_pred = model_breast.predict([[mean_radius, mean_texture, mean_perimeter, mean_area, mean_smoothness, mean_compactness, mean_concavity, mean_concave_points, 
                                 mean_symmetry, mean_fractal_dimension, radius_error, texture_error, perimeter_error, area_error, smoothness_error, compactness_error, 
                                 concavity_error, concave_points_error, symmetry_error, fractal_dimension_error, worst_radius, worst_texture, worst_perimeter,
                                 worst_area, worst_smoothness, worst_compactness, worst_concavity, worst_concave_points, worst_symmetry, worst_fractal_dimension]])
        if y_pred[0] == 0:
            y_pred = 'Malignant'
        else:
            y_pred = 'Benign'
        return render(request, 'hospital/breast-cancer-prediction.html', {'result' : y_pred})
    return render(request, 'hospital/breast-cancer-prediction.html', )

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def heart_disease_prediction(request):
    if request.method == 'POST':
        age = float(request.POST['age'])
        sex = (request.POST['sex'])
        if sex == "Male":
            sex = 1
        else:
            sex = 0
        cp = (request.POST['cp'])
        if cp == "Typical Angina":
            cp = 1
        elif cp == "ATypical Angina":
            cp = 2
        elif cp == "Non-Anginal Pain":
            cp = 3
        else:
            cp = 4
        trestbps = float(request.POST['trestbps'])
        chol = float(request.POST['chol'])
        fbs = float(request.POST['fbs'])
        restecg = float(request.POST['restecg'])
        thalach = float(request.POST['thalach'])
        exang = float(request.POST['exang'])
        oldpeak = float(request.POST['oldpeak'])
        slope = float(request.POST['slope'])
        ca = float(request.POST['ca'])
        thal = float(request.POST['thal'])
        y_pred = model_heart.predict([[age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]])
        if y_pred[0] == 0:
            y_pred = 'The Person Does Not Have A Heart Disease.'
        else:
            y_pred = 'The Person Has Heart Disease'
        return render(request, 'hospital/heart-disease-prediction.html', {'result' : y_pred})
    return render(request, 'hospital/heart-disease-prediction.html', )

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def depression_prediction(request):
    if request.method == 'POST':
        sex = (request.POST['sex'])
        if sex == "Male":
            sex = 1
        else:
            sex = 0
        age = float(request.POST['age'])
        married = (request.POST['married'])
        if married == "Yes":
            married = 1
        else:
            married = 0
        number_of_children = float(request.POST['number_of_children'])
        total_members = float(request.POST['total_members'])
        asset_value = float(request.POST['asset_value'])
        living_expenses = float(request.POST['living_expenses'])
        income = (request.POST['income'])
        if income == "Yes":
            income = 1
        else:
            income = 0
        investment = float(request.POST['investment'])
        y_pred = model_depression.predict([[sex, age, married, number_of_children, total_members, asset_value, living_expenses, income, investment]])
        if y_pred[0] == 0:
            y_pred = 'You are not suffering from depression.'
        else:
            y_pred = 'You are suffering from depression.'
        return render(request, 'hospital/depression-prediction.html', {'result' : y_pred})
    return render(request, 'hospital/depression-prediction.html', )

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def stroke_prediction(request):
    if request.method == 'POST':
        gender = (request.POST['gender'])
        if gender == "Male":
            gender = 1
        else:
            gender = 0
        age = float(request.POST['age'])
        hypertension = (request.POST['hypertension'])
        if hypertension == "Yes":
            hypertension = 1
        else:
            hypertension = 0
        heart = (request.POST['heart'])
        if heart == "Yes":
            heart = 1
        else:
            heart = 0
        marriage = (request.POST['marriage'])
        if marriage == "Yes":
            marriage = 1
        else:
            marriage = 0
        work = (request.POST['work'])
        if work == "Children":
            work = 1
        elif work == "Government Job":
            work = 2
        elif work == "Never Worked":
            work = 3
        elif work == "Private":
            work = 4
        else:
            work = 5
        residence = (request.POST['residence'])
        if residence == "Rural":
            residence = 1
        else:
            residence = 2
        glucose = float(request.POST['glucose'])
        bmi = float(request.POST['bmi'])
        smoking = (request.POST['smoking'])
        if smoking == "Formerly Smoke":
            smoking = 1
        elif smoking == "Never Smoked":
            smoking = 2
        else:
            smoking = 3
        y_pred = model_stroke.predict([[gender, age, hypertension, heart, marriage, work, residence, glucose, bmi, smoking]])
        if y_pred[0] == 0:
            y_pred = 'Stroke can happen.'
        else:
            y_pred = 'Less Chances of Stroke'
        return render(request, 'hospital/stroke-prediction.html', {'result' : y_pred})
    return render(request, 'hospital/stroke-prediction.html', )

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def diabetes_prediction(request):
    if request.method == 'POST':
        pregnancies = float(request.POST['pregnancies'])
        glucose = float(request.POST['glucose'])
        blood_pressure = float(request.POST['blood_pressure'])
        skin_thickness = float(request.POST['skin_thickness'])
        insulin = float(request.POST['insulin'])
        bmi = float(request.POST['bmi'])
        diabetes_pedigree_function = float(request.POST['diabetes_pedigree_function'])
        age = float(request.POST['age'])
        y_pred = model_diabetes.predict([[pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, age]])
        if y_pred[0] == 1:
            y_pred = 'Patient is Diabetic.'
        else: 
            y_pred = 'Patient is not diabetic.'
        return render(request, 'hospital/diabetes-prediction.html', {'result' : y_pred})
    return render(request, 'hospital/diabetes-prediction.html', )

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def lung_prediction(request):
    if request.method == 'POST':
        age = float(request.POST['age'])
        smoking = (request.POST['smoking'])
        if smoking == "Yes":
            smoking = 2
        else:
            smoking = 1
        yellow_fingers = (request.POST['yellow_fingers'])
        if yellow_fingers == "Yes":
            yellow_fingers = 2
        else:
            yellow_fingers = 1
        anxiety = (request.POST['anxiety'])
        if anxiety == "Yes":
            anxiety = 2
        else:
            anxiety = 1
        peer_pressure = (request.POST['peer_pressure'])
        if peer_pressure == "Yes":
            peer_pressure = 2
        else:
            peer_pressure = 1
        chronic_disease = (request.POST['chronic_disease'])
        if chronic_disease == "Yes":
            chronic_disease = 2
        else:
            chronic_disease = 1
        fatigue = (request.POST['fatigue'])
        if fatigue == "Yes":
            fatigue = 2
        else:
            fatigue = 1
        allergy = (request.POST['allergy'])
        if allergy == "Yes":
            allergy = 2
        else:
            allergy = 1
        wheezing = (request.POST['wheezing'])
        if wheezing == "Yes":
            wheezing = 2
        else:
            wheezing = 1
        alcohol_consuming = (request.POST['alcohol_consuming'])
        if alcohol_consuming == "Yes":
            alcohol_consuming = 2
        else:
            alcohol_consuming = 1
        coughing = (request.POST['coughing'])
        if coughing == "Yes":
            coughing = 2
        else:
            coughing = 1
        shortness_of_breath = (request.POST['shortness_of_breath'])
        if shortness_of_breath == "Yes":
            shortness_of_breath = 2
        else:
            shortness_of_breath = 1
        swallowing_difficulty = (request.POST['swallowing_difficulty'])
        if swallowing_difficulty == "Yes":
            swallowing_difficulty = 2
        else:
            swallowing_difficulty = 1
        chest_pain = (request.POST['chest_pain'])
        if chest_pain == "Yes":
            chest_pain = 2
        else:
            chest_pain = 1
        y_pred = model_lung.predict([[age, smoking, yellow_fingers, anxiety, peer_pressure, chronic_disease, fatigue, allergy, wheezing,
                                        alcohol_consuming, coughing, shortness_of_breath, swallowing_difficulty, chest_pain]])
        if y_pred[0] == 'YES':
            y_pred = 'Lung Cancer is present.'
        else:
            y_pred = 'Lung Cancer is absent.'
        return render(request, 'hospital/lung-cancer-prediction.html', {'result' : y_pred})
    return render(request, 'hospital/lung-cancer-prediction.html', )

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def fetal_health_prediction(request):
    if request.method == 'POST':
        baseline_value = float(request.POST['baseline_value'])
        accelerations = float(request.POST['accelerations'])
        fetal_movement = float(request.POST['fetal_movement'])
        uterine_contractions = float(request.POST['uterine_contractions'])
        light_decelerations = float(request.POST['light_decelerations'])
        severe_decelerations = float(request.POST['severe_decelerations'])
        prolongued_decelerations = float(request.POST['prolongued_decelerations'])
        abnormal_short_term_variability = float(request.POST['abnormal_short_term_variability'])
        mean_value_of_short_term_variability = float(request.POST['mean_value_of_short_term_variability'])
        percentage_of_time_with_abnormal_long_term_variability = float(request.POST['percentage_of_time_with_abnormal_long_term_variability'])
        mean_value_of_long_term_variability = float(request.POST['mean_value_of_long_term_variability'])
        histogram_width = float(request.POST['histogram_width'])
        histogram_min = float(request.POST['histogram_min'])
        histogram_max = float(request.POST['histogram_max'])
        histogram_number_of_peaks = float(request.POST['histogram_number_of_peaks'])
        histogram_number_of_zeroes = float(request.POST['histogram_number_of_zeroes'])
        histogram_mode = float(request.POST['histogram_mode'])
        histogram_mean = float(request.POST['histogram_mean'])
        histogram_median = float(request.POST['histogram_median'])
        histogram_variance = float(request.POST['histogram_variance'])
        histogram_tendency = float(request.POST['histogram_tendency'])
        prediction = model_fetal.predict([[baseline_value, accelerations, fetal_movement, uterine_contractions, 
                                           light_decelerations, severe_decelerations, prolongued_decelerations,
                                           abnormal_short_term_variability, mean_value_of_short_term_variability,
                                           percentage_of_time_with_abnormal_long_term_variability, mean_value_of_long_term_variability,
                                           histogram_width, histogram_min, histogram_max, histogram_number_of_peaks,
                                           histogram_number_of_zeroes, histogram_mode, histogram_mean, histogram_median,
                                           histogram_variance, histogram_tendency]])
        if prediction == 1:
            y_pred = 'Fetal is normal.'
        elif prediction == 2:
            y_pred = 'Fetal is suspect.'
        else:
            y_pred = 'Fetal is pathological.'
        return render(request, 'hospital/fetal-health-prediction.html', {'result' : y_pred})
    return render(request, 'hospital/fetal-health-prediction.html', )

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            phone = sub.cleaned_data['Phone']
            email = EmailMessage(
                subject= f"{name} from Medical Mind. || {phone}",
                body = message,
                from_email=settings.EMAIL_HOST_USER,
                to=[settings.EMAIL_HOST_USER],
                reply_to=[email]
            )
            email.send()
            return render(request, 'hospital/contactussuccess.html')
    return render(request, 'hospital/contactus.html', {'form':sub})