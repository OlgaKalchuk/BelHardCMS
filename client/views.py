from django.shortcuts import redirect, render, get_object_or_404
from django.template.context_processors import csrf
from django.http import HttpResponse
from django.urls import reverse
from django.views import View
from django.http import HttpResponse


from .forms import UploadImgForm, AddSkillForm, AddSkillFormSet, OpinionForm, AnswerForm, MessageForm

from BelHardCRM.settings import MEDIA_URL
from .forms import UploadImgForm, EducationFormSet, CertificateFormSet, inlineEduCert
from .models import *
from .utility import *

from django.views.generic import View
from django.contrib import auth


def client_main_page(request):
    response = csrf(request)
    response['client_img'] = load_client_img(request.user)
    readtask = len(Tasks.objects.filter(user = request.user, readtask = False))
    chat = Chat.objects.get(members=request.user)
    unread_messages = len(Message.objects.filter(chat=chat, is_read=False).exclude(author=request.user))
    context = {'response': response, 'unread_messages': unread_messages, 'readtask' : readtask}
    return render(request=request, template_name='client/client_main_page.html', context=context)



def client_profile(request):
    response = csrf(request)
    response['client_img'] = load_client_img(request.user)

    return render(request=request, template_name='client/client_profile.html', context=response)


def client_edit_main(request):
    response = csrf(request)

    """ Загрузка из БД списков для выбора """
    response['client_img'] = load_client_img(request.user)
    response['sex'] = Sex.objects.all()
    response['citizenship'] = Citizenship.objects.all()
    response['family_state'] = reversed(FamilyState.objects.all())
    response['children'] = reversed(Children.objects.all())
    response['country'] = response['citizenship']
    response['city'] = reversed(City.objects.all())
    response['state'] = reversed(State.objects.all())

    if request.method == 'POST':
        print('client_edit_main - request.POST')

        """ Входные данные для сохранения: """
        user = request.user
        user_name = check_input_str(request.POST['client_first_name'])
        last_name = check_input_str(request.POST['client_last_name'])
        patronymic = check_input_str(request.POST['client_middle_name'])
        sex = Sex.objects.get(sex_word=request.POST['sex'])
        date = request.POST['date_born']
        citizenship = Citizenship.objects.get(country_word=request.POST['citizenship'])
        family_state = FamilyState.objects.get(state_word=request.POST['family_state'])
        children = Children.objects.get(children_word=request.POST['children'])
        country = Citizenship.objects.get(country_word=request.POST['country'])
        city = City.objects.get(city_word=request.POST['city'])
        street = check_input_str(request.POST['street'])
        house = check_home_number(request.POST['house'])
        flat = check_home_number(request.POST['flat'])
        telegram_link = check_telegram(request.POST['telegram_link'])
        skype = check_input_str(request.POST['skype_id'])
        email = request.POST['email']
        link_linkedin = request.POST['link_linkedin']
        state = State.objects.get(state_word=request.POST['state'])

        print(user_name, last_name, patronymic, sex, date, citizenship, family_state, children, country, city,
              street, house, flat, telegram_link, skype, email, link_linkedin, state)

        """ проверка - сохранена ли карточка клиента в БД. 
        users_id_list - список карточек c id клиента. """
        users_id_list = [i['user_client_id'] for i in Client.objects.all().values()]
        print("users_id_list: %s" % users_id_list)

        if user.id not in users_id_list:
            """ Если карточки нету - создаём. """
            print('User Profile DO NOT exists - creating!')

            client = Client(
                user_client=user,
                name=user_name,
                lastname=last_name,
                patronymic=patronymic,
                sex=sex,
                date_born=date if date else None,
                citizenship=citizenship,
                family_state=family_state,
                children=children,
                country=country,
                city=city,
                street=street,
                house=house,
                flat=flat,
                telegram_link=telegram_link,
                skype=skype,
                email=email,
                link_linkedin=link_linkedin,
                state=state,
            )
            client.save()
        else:
            """ Если карточка есть - достаём из БД Объект = Клиент_id.
            Перезаписываем (изменяем) существующие данныев. """
            print('User Profile exists - Overwriting user data')

            client = Client.objects.get(user_client=user)  # Объект = Клиент_id

            client.name = user_name
            client.lastname = last_name
            client.patronymic = patronymic
            client.sex = sex
            client.date_born = date if date else None
            client.citizenship = citizenship
            client.family_state = family_state
            client.children = children
            client.country = country
            client.city = city
            client.street = street
            client.house = house
            client.flat = flat
            client.telegram_link = telegram_link
            client.skype = skype
            client.email = email
            client.link_linkedin = link_linkedin
            client.state = state
            client.save()

        """ Сохранение телефонных номеров клиента """
        tel = request.POST.getlist('phone')
        print("tel: %s" % tel)
        for t in tel:
            t = check_phone(t)
            if t:
                phone = Telephone(telephone_number=t)
                phone.client = client
                phone.save()

        print('client_edit_main - OK')
        return redirect(to='/client/profile')
    else:
        print('client_edit_main - request.GET')

    return render(request=request, template_name='client/client_edit_main.html', context=response)


def client_edit_skills(request):
    response = csrf(request)
    response['client_img'] = load_client_img(request.user)

    if request.method == 'POST':
        print("client_edit_skills - request.POST")

        skills_arr = request.POST.getlist('skill')
        print("skill: %s" % skills_arr)

        for s in skills_arr:
            if s:
                skill = Skills(skills=check_input_str(s))
                skill.save()

                """ ОБЪЕДИНЕНИЕ модуля Навыки с конкретным залогиненым клиентом!!! """
                client = Client.objects.get(user_client=request.user)
                client.skills = skill
                client.save()

        return redirect(to='/client/edit')
    else:
        print('client_edit_skills - request.GET')

    return render(request=request, template_name='client/client_edit_skills.html', context=response)


def client_edit_photo(request):
    response = csrf(request)
    response['client_img'] = load_client_img(request.user)

    if request.method == 'POST':
        print('client_edit_photo - request.POST')

        form = UploadImgForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.cleaned_data.get('img')
            client = Client.objects.get(user_client=request.user)
            client.img = img
            client.save()
            """
            в БД сохраняется УНИКАЛЬНОЕ имя картинки (пр. user_2_EntrmQR.png)
            в папке MEDIA_URL = '/media/'
            """
            print('client save photo - OK')
            return redirect(to='/client/edit')
    else:
        print('client_edit_photo - request.GET')
        response['form'] = UploadImgForm()

    return render(request=request, template_name='client/client_edit_photo.html', context=response)


def client_edit_cv(request):
    response = csrf(request)
    response['client_img'] = load_client_img(request.user)

    if request.method == 'POST':
        print('client_edit_cv - request.POST')

        arr_cv = pars_cv_request(request.POST)
        for cvs in arr_cv:
            position = cvs['position']
            employment_word = cvs['employment']
            employment = Employment(employment=employment_word)
            employment.save()
            time_job_word = cvs['time_job']
            time_job = TimeJob(time_job_word=time_job_word)
            time_job.save()
            salary = cvs['salary']
            type_word = cvs['type_salary']
            type_salary = TypeSalary(type_word=type_word)
            type_salary.save()

            if any([position, employment_word, time_job_word, salary, type_word]):
                cv = CV(
                    position=position,
                    employment=employment,
                    time_job=time_job,
                    salary=salary,
                    type_salary=type_salary,
                )
                cv.save()

                client = Client.objects.get(user_client=request.user)
                client.cv = cv
                client.save()

                print("CV Form - OK\n", position, employment, time_job, salary, type_salary)
            else:
                print('Cv form is Empty')

        return redirect(to='/client/edit')
    else:
        print('client_edit_cv - request.GET')

    return render(request, 'client/client_edit_cv.html', response)


def client_edit_education(request):
    response = csrf(request)
    response['client_img'] = load_client_img(request.user)

    if request.method == 'POST':
        print("save_client_education - request.POST")

        arr_edu = pars_edu_request(request.POST, request.FILES)
        for edus in arr_edu:
            university = edus['education']
            subject_area = edus['subject_area']
            specialization = edus['specialization']
            qualification = edus['qualification']
            date_start = edus['date_start']
            date_end = edus['date_end']

            img_name = None
            try:
                img = edus['certificate_img']
                img_name = str(img)
                with open(MEDIA_URL + img_name, 'wb+') as file:
                    for chunk in img.chunks():
                        file.write(chunk)
            except:
                logging.error("Ex. in cer_img save")

            link = edus['certificate_url']

            if any([university, subject_area, specialization, qualification,
                    date_start, date_end, img_name, link]):
                certificate = Certificate(
                    img=img_name,
                    link=link
                )
                certificate.save()

                education = Education(
                    education=university,
                    subject_area=subject_area,
                    specialization=specialization,
                    qualification=qualification,
                    date_start=date_start if date_start else None,
                    date_end=date_end if date_end else None,
                    certificate=certificate
                )
                education.save()

                client = Client.objects.get(user_client=request.user)
                client.education = education
                client.save()

                print("Education Form - OK\n", university, subject_area, specialization, qualification,
                      date_start if date_start else None, date_end if date_end else None, img_name, link)
            else:
                print('Education Form is Empty')

        return redirect('/client/edit')
    else:
        print('client_edit_education - request.GET')

    return render(request, 'client/client_edit_education.html', response)


def client_edit_experience(request):
    response = csrf(request)
    response['client_img'] = load_client_img(request.user)

    if request.method == 'POST':
        print("save_client_edit_experience - request POST")

        arr = pars_exp_request(request.POST)
        for dic in arr:
            organisation = dic['experience_1']
            position = dic['experience_3']
            start_date = dic['exp_date_start']
            end_date = dic['exp_date_end']
            duties = dic['experience_4']

            if any([organisation, position, start_date, end_date, duties]):
                experiences = Experience(
                    name=organisation,
                    position=position,
                    start_date=start_date if start_date else None,
                    end_date=end_date if end_date else None,
                    duties=duties if duties else None
                )
                experiences.save()

                spheres = dic['experience_2']
                for s in spheres:
                    if s:
                        """ Save ManyToManyField 'sphere' """
                        sp = Sphere(sphere_word=s)
                        sp.save()
                        experiences.sphere.add(sp)

                client = Client.objects.get(user_client=request.user)
                client.organization = experiences
                client.save()

                print("Experience Form - OK\n", organisation, spheres, position, start_date if start_date else None,
                      end_date if end_date else None, duties if duties else None)
            else:
                print('Experience Form is Empty')

        return redirect('/client/edit')
    else:
        print('save_client_edit_experience - request GET')

    return render(request, 'client/client_edit_experience.html', response)


class MessagesView(View):
    def get(self, request):
        try:
            chat = Chat.objects.get(members=request.user)
            if request.user in chat.members.all():
                chat.message_set.filter(is_read=False).exclude(author=request.user).update(is_read=True)
            else:
                chat = None
        except Chat.DoesNotExist:
            chat = None

        unread_messages = len(Message.objects.filter(chat=chat, is_read=False).exclude(author=request.user))
        context = {'user_profile': request.user, 'unread_messages': unread_messages, 'chat': chat, 'form': MessageForm()}

        return render(request, 'client/client_chat.html', context)

    def post(self, request):
        form = MessageForm(data=request.POST)
        chat = Chat.objects.get(members=request.user)
        print(form)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat_id = chat.id
            message.author = request.user
            message.save()
        return redirect(reverse('contact_with_centre'))


def opinion_list(request):
    opinion = Opinion.objects.all()
    return render(request, 'opinion/index.html', context={'opinion' : opinion})

def answer_create(request, pk):
    opinion = get_object_or_404(Opinion, id=pk)
    answer = Answer.objects.filter(pk = pk)
    form = AnswerForm()

    if request.method == "POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.opinion = opinion
            form.user = request.user
            form.save()
            return redirect('opinion_detail', pk)
    return render(request, 'opinion/answer_create.html', context={'form':form, 'opinion':opinion, "answer" : answer})

class OpinionCreate(View):
    def get(self, request):
        form = OpinionForm()
        return render(request,'opinion/opinion_create.html', context={'form':form})

    def post(self, request):
        form = OpinionForm(request.POST)

        if form.is_valid():
            new_opinion = form.save(commit=False)
            new_opinion.user = request.user
            new_opinion.save()
            return redirect('opinion_detail', pk = new_opinion.pk)
        return render(request, 'opinion/opinion_create.html', context={'form' : form})

def opinion_detail(request, pk):
    opinion = get_object_or_404(Opinion, pk=pk)
    return render(request, 'opinion/opinion_detail.html', {'opinion': opinion})


class OpinionDelete(View):
    def get(self, request, pk):
        opinion = Opinion.objects.filter(pk = pk)
        return render(request, 'opinion/opinion_delete.html', context={'opinion' : opinion})

    def post(self, request, pk):
        opinion = Opinion.objects.filter(pk = pk)
        opinion.delete()
        return redirect(reverse('opinion_list'))



def client_login(request):      #ввести логин/пароль -> зайти в систему
    res = csrf(request)
    res['url'] = 'login'
    if request.POST:
        password = request.POST['password']
        user = request.POST['user']
        u = auth.authenticate(username=user, password=password)
        if u:
            auth.login(request, u)
            return redirect('/')               #переадресация после авторизации
        else:
            res['error'] = "Неверный login/пароль"
            return render(request, 'registration.html', res)
    else:
        return render(request, 'registration.html', res)


def client_logout(request):     #выйти из системы, возврат на стартовую страницу
    auth.logout(request)
    return redirect('/')      #вставить редирект куда требуется


def tasks(request):
    task = Tasks.objects.filter(user=request.user, status=False)
    task_false = Tasks.objects.filter(user=request.user, status=True) #status=False)
    task_false = sorted(task_false, key=lambda x:x.endtime,  reverse=True)



    return render(request, 'client/tasks.html', context = {'task' : task,  'task_false': task_false})


def form_education(request):
    """ Test Code - Module Form Set """
    response = csrf(request)
    response['client_img'] = load_client_img(request.user)

    if request.method == 'POST':
        print(request.POST)

        cert_inst = None
        form_set_cert = CertificateFormSet(request.POST, request.FILES)
        if form_set_cert.is_valid():
            print("FormSet_Cert - OK")
            for c in form_set_cert:
                c_items = c.cleaned_data.items()
                print('cert_items: %s' % c_items)
                if c_items:
                    cert_inst = c.save(commit=False)
                    # cert_inst.evidence_of_edu.save_m2m()
                    cert_inst.save()
        else:
            print("FormSet_Cert not Valid")

        form_set_edu = EducationFormSet(request.POST)
        if form_set_edu.is_valid():
            print('FormSet_Edu - OK')
            for f in form_set_edu:
                f_items = f.cleaned_data.items()
                print("edu_items: %s" % f_items)
                if f_items:
                    """ edu_inst - unsaved model instance!
                    It gives you ability to attach data to the instance before saving to the DB! """
                    edu_inst = f.save(commit=False)
                    """ attach ForeignKey == Certificate instance """
                    edu_inst.certificate = cert_inst
                    """ Save Education instance """
                    edu_inst.save()

                    client = Client.objects.get(user_client=request.user)
                    """ attach Edu.Inst to the client, because Client has ForeignKey to Edu-n """
                    client.education = edu_inst
                    client.save()
                    """ saving this shit and going to sleep (02:30 here :P)"""
        else:
            print('FormSet_Edu not valid')

        return redirect(to='/client/edit/form_edu')
    else:
        response['edu_form'] = EducationFormSet()
        response['certificate'] = CertificateFormSet()
        response['inlineEduCert'] = inlineEduCert()

    return render(request, 'client/form_edu.html', response)


def load_client_img(req):
    """ Show Client Img in the Navigation Bar.
    Img loaded from DB, if user do not have img - load default. """
    try:
        print("user: %s, id: %s" % (req, req.id))
        client_img = Client.objects.get(user_client=req).img
        if client_img:
            logging.info("Client.img: %s" % client_img)
            return "%s%s" % (MEDIA_URL, client_img)
        else:
            return '/media/user_1.png'
    except Exception as ex:
        logging.error("Exception in - load_client_img()\n %s" % ex)
        return '/media/user_1.png'


def checktask(request):
    id = (request.GET['id'])
    task = Tasks.objects.get(id=id)

    if task.status == False:
        task.status = True
        task.endtime = timezone.now()
    else:
        task.status = False
        task.endtime = None
    task.save()
    return HttpResponse(task)

def checknotifications(request):
    chat = Chat.objects.get(members=request.user)
    unread_messages = len(Message.objects.filter(chat=chat, is_read=False).exclude(author=request.user))

    return HttpResponse(unread_messages)

def set_settings(request):
    #request.GET
    return HttpResponse()

