import logging

from django.shortcuts import render,redirect
from django.contrib.auth.models import User,auth
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMessage
from .models import *

from .models import Comment,Post
# Create your views here.

logger = logging.getLogger(__name__)


def _request_id(request):
    return getattr(request, "request_id", "unknown")

def _post_queryset():
    return Post.objects.select_related("category", "user")

def index(request):
    return render(request,"index.html",{
        'posts':_post_queryset().filter(user_id=request.user.id).order_by("-id") if request.user.is_authenticated else Post.objects.none(),
        'top_posts':_post_queryset().order_by("-likes"),
        'recent_posts':_post_queryset().order_by("-id"),
        'user':request.user,
        'media_url':settings.MEDIA_URL
    })


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password == password2:
            if User.objects.filter(username=username).exists():
                logger.warning("signup_rejected request_id=%s reason=username_exists", _request_id(request))
                messages.info(request,"Username already Exists")
                return redirect('signup')
            if User.objects.filter(email=email).exists():
                logger.warning("signup_rejected request_id=%s reason=email_exists", _request_id(request))
                messages.info(request,"Email already Exists")
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username,email=email,password=password)
                user.save()
                logger.info("signup_succeeded request_id=%s user_id=%s", _request_id(request), user.pk)
                return redirect('signin')
        else:
            logger.warning("signup_rejected request_id=%s reason=password_mismatch", _request_id(request))
            messages.info(request,"Password should match")
            return redirect('signup')
            
    return render(request,"signup.html")

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request,username=username,password=password)
        if user is not None:
            auth.login(request,user)
            logger.info("signin_succeeded request_id=%s user_id=%s", _request_id(request), user.pk)
            return redirect("index")
        else:
            logger.warning("signin_failed request_id=%s", _request_id(request))
            messages.info(request,'Username or Password is incorrect')
            return redirect("signin")
            
    return render(request,"signin.html")

def logout(request):
    user_id = request.user.pk if request.user.is_authenticated else "anonymous"
    auth.logout(request)
    logger.info("logout_succeeded request_id=%s user_id=%s", _request_id(request), user_id)
    return redirect('index')

def blog(request):
    return render(request,"blog.html",{
            'posts':_post_queryset().filter(user_id=request.user.id).order_by("-id") if request.user.is_authenticated else Post.objects.none(),
            'top_posts':_post_queryset().order_by("-likes"),
            'recent_posts':_post_queryset().order_by("-id"),
            'user':request.user,
            'media_url':settings.MEDIA_URL
        })
    
def create(request):
    if request.method == 'POST':
        try:
            postname = request.POST['postname']
            content = request.POST['content']
            category_id = request.POST['category']
            category = Category.objects.get(id=category_id)
            image = request.FILES.get('image')
            created_post = Post(postname=postname, content=content, category=category, image=image, user=request.user)
            created_post.save()
            logger.info(
                "post_created request_id=%s post_id=%s user_id=%s has_image=%s",
                _request_id(request),
                created_post.pk,
                request.user.pk,
                bool(image),
            )
        except Exception:
            logger.exception(
                "post_create_failed request_id=%s user_id=%s",
                _request_id(request),
                getattr(request.user, "pk", None),
            )
        return redirect('index')
    else:
        categories = Category.objects.all()
        return render(request, "create.html", {"categories": categories})
    
def profile(request,id):
    
    return render(request,'profile.html',{
        'user':User.objects.get(id=id),
        'posts':Post.objects.all(),
        'media_url':settings.MEDIA_URL,
    })
    
    
def profileedit(request,id):
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
    
        user = User.objects.get(id=id)
        user.first_name = firstname
        user.email = email
        user.last_name = lastname
        user.save()
        logger.info(
            "profile_updated request_id=%s user_id=%s actor_user_id=%s",
            _request_id(request),
            user.pk,
            getattr(request.user, "pk", None),
        )
        return profile(request,id)
    return render(request,"profileedit.html",{
        'user':User.objects.get(id=id),
    })
    
def increaselikes(request,id):
    if request.method == 'POST':
        post = Post.objects.get(id=id)
        post.likes += 1
        post.save() 
        logger.info("post_liked request_id=%s post_id=%s", _request_id(request), post.pk)
    return redirect(request.META.get("HTTP_REFERER", "index"))


def post(request,id):
    post = _post_queryset().get(id=id)
    
    return render(request,"post-details.html",{
        "user":request.user,
        'post':post,
        'recent_posts':_post_queryset().exclude(id=id).order_by("-id"),
        'media_url':settings.MEDIA_URL,
        'comments':Comment.objects.select_related("user").filter(post_id = post.id),
        'total_comments': Comment.objects.filter(post_id = post.id).count()
    })
    
def savecomment(request,id):
    post = Post.objects.get(id=id)
    if request.method == 'POST':
        content = request.POST['message']
        comment = Comment(post_id = post.id,user_id = request.user.id, content = content)
        comment.save()
        logger.info(
            "comment_created request_id=%s comment_id=%s post_id=%s user_id=%s",
            _request_id(request),
            comment.pk,
            post.pk,
            request.user.pk,
        )
        return redirect("index")
    
def deletecomment(request,id):
    comment = Comment.objects.get(id=id)
    postid = comment.post.id
    comment_id = comment.pk
    comment.delete()
    logger.info(
        "comment_deleted request_id=%s comment_id=%s post_id=%s user_id=%s",
        _request_id(request),
        comment_id,
        postid,
        getattr(request.user, "pk", None),
    )
    return post(request,postid)
    
def editpost(request, id):
    post = Post.objects.get(id=id)
    if request.method == 'POST':
        try:
            postname = request.POST['postname']
            content = request.POST['content']
            category_id = request.POST['category']
            category = Category.objects.get(id=category_id)  # Fetch the Category object
            
            post.postname = postname
            post.content = content
            post.category = category  # Assign the Category object
            post.save()
            logger.info(
                "post_updated request_id=%s post_id=%s user_id=%s",
                _request_id(request),
                post.pk,
                getattr(request.user, "pk", None),
            )
        except Exception:
            logger.exception(
                "post_update_failed request_id=%s post_id=%s user_id=%s",
                _request_id(request),
                post.pk,
                getattr(request.user, "pk", None),
            )
        return profile(request, request.user.id)
    
    categories = Category.objects.all()  # Fetch all categories for the dropdown
    return render(request, "postedit.html", {
        'post': post,
        'categories': categories
    })
    
def deletepost(request,id):
    deleted_post = Post.objects.get(id=id)
    deleted_post.delete()
    logger.info(
        "post_deleted request_id=%s post_id=%s user_id=%s",
        _request_id(request),
        id,
        getattr(request.user, "pk", None),
    )
    return profile(request,request.user.id)


def contact_us(request):
    context = {}
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        messenger = request.POST.get('messenger', '').strip()
        message = request.POST.get('message', '').strip()
        answer_files = request.FILES.getlist("answer_files")

        allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".heic", ".doc", ".docx"}
        total_size = sum(upload.size for upload in answer_files)
        errors = []

        logger.info(
            "contact_submission_received request_id=%s file_count=%s total_bytes=%s",
            _request_id(request),
            len(answer_files),
            total_size,
        )

        if not answer_files:
            errors.append("Додайте файл з відповідями: фото, скріншот, PDF або документ.")

        for upload in answer_files:
            file_name = upload.name.lower()
            if not any(file_name.endswith(extension) for extension in allowed_extensions):
                errors.append(f"Файл {upload.name} має непідтримуваний формат.")
            if upload.size > settings.CONTACT_UPLOAD_MAX_SIZE:
                errors.append(f"Файл {upload.name} більший за дозволений розмір.")

        if total_size > settings.CONTACT_UPLOAD_MAX_TOTAL_SIZE:
            errors.append("Загальний розмір файлів завеликий. Спробуйте надіслати менше файлів або стиснути фото.")

        if errors:
            logger.warning(
                "contact_submission_rejected request_id=%s error_count=%s file_count=%s total_bytes=%s",
                _request_id(request),
                len(errors),
                len(answer_files),
                total_size,
            )
            context["errors"] = errors
            context["form_data"] = request.POST
        else:
            subject = "Запит на навчання: діагностичний тест"
            file_names = ", ".join(upload.name for upload in answer_files)
            saved_message = (
                f"Instagram або Telegram: {messenger or 'не вказано'}\n\n"
                f"Повідомлення:\n{message or 'не вказано'}\n\n"
                f"Файли з відповідями: {file_names}"
            )

            contact = Contact(name=name, email=email, subject=subject, message=saved_message)
            contact.save()
            logger.info(
                "contact_submission_saved request_id=%s contact_id=%s file_count=%s total_bytes=%s",
                _request_id(request),
                contact.pk,
                len(answer_files),
                total_size,
            )

            email_message = EmailMessage(
                subject=f"[Olena Khandii] {subject}",
                body=(
                    "Новий запит на навчання після діагностичного тесту.\n\n"
                    f"Ім'я: {name}\n"
                    f"Email: {email}\n"
                    f"Instagram або Telegram: {messenger or 'не вказано'}\n\n"
                    f"Повідомлення:\n{message or 'не вказано'}\n\n"
                    f"Файли: {file_names}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.TEACHER_EMAIL],
                reply_to=[email] if email else None,
            )

            logger.info(
                "contact_email_attachments_started request_id=%s contact_id=%s attachment_count=%s total_bytes=%s",
                _request_id(request),
                contact.pk,
                len(answer_files),
                total_size,
            )
            for upload in answer_files:
                email_message.attach(upload.name, upload.read(), upload.content_type)
            logger.info(
                "contact_email_attachments_completed request_id=%s contact_id=%s attachment_count=%s",
                _request_id(request),
                contact.pk,
                len(answer_files),
            )

            try:
                logger.info(
                    "contact_email_send_started request_id=%s contact_id=%s attachment_count=%s total_bytes=%s backend=%s smtp_host=%s smtp_port=%s tls=%s ssl=%s",
                    _request_id(request),
                    contact.pk,
                    len(answer_files),
                    total_size,
                    settings.EMAIL_BACKEND,
                    settings.EMAIL_HOST or "-",
                    settings.EMAIL_PORT,
                    settings.EMAIL_USE_TLS,
                    settings.EMAIL_USE_SSL,
                )
                sent_count = email_message.send(fail_silently=False)
                logger.info(
                    "contact_email_send_succeeded request_id=%s contact_id=%s sent_count=%s",
                    _request_id(request),
                    contact.pk,
                    sent_count,
                )
                context["success_message"] = (
                    "Дякую! Відповіді надіслано. Я перегляну тест і напишу вам щодо наступного кроку."
                )
            except Exception:
                logger.exception(
                    "contact_email_send_failed request_id=%s contact_id=%s attachment_count=%s total_bytes=%s",
                    _request_id(request),
                    contact.pk,
                    len(answer_files),
                    total_size,
                )
                context["errors"] = [
                    "Заявку збережено, але лист не вдалося надіслати. Будь ласка, напишіть напряму на email викладача."
                ]

    return render(request,"contact.html", context)

def booking(request):
    return render(request,"calendar_integration.html",{})

def services(request):
    return render(request,"services.html",{})

def prices(request):
    return render(request,"prices.html",{})

def rules(request):
    return render(request,"rules.html",{})

def free_materials(request):
    return render(request,"free-materials.html",{})

def schedule(request):
    return render(request,"schedule.html",{})

def aboutme(request):
    return render(request,"about.html",{})

def reviews(request):
    return redirect(settings.INSTAGRAM_REVIEWS_URL)
