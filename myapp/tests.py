from unittest.mock import patch

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.contrib.auth.models import User
from .models import Post, Category, Comment, Contact

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category", description="Test Description")

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Test Category")
        self.assertEqual(self.category.description, "Test Description")
        self.assertEqual(str(self.category), "Test Category")


class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Test Category")
        self.post = Post.objects.create(
            postname="Test Post",
            category=self.category,
            content="Test Content",
            user=self.user,
        )

    def test_post_creation(self):
        self.assertEqual(self.post.postname, "Test Post")
        self.assertEqual(self.post.content, "Test Content")
        self.assertEqual(self.post.category.name, "Test Category")
        self.assertEqual(str(self.post), "Test Post")


class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Test Category")
        self.post = Post.objects.create(
            postname="Test Post",
            category=self.category,
            content="Test Content",
            user=self.user,
        )
        self.comment = Comment.objects.create(
            content="Test Comment", post=self.post, user=self.user
        )

    def test_comment_creation(self):
        self.assertEqual(self.comment.content, "Test Comment")
        self.assertEqual(self.comment.post.postname, "Test Post")
        self.assertEqual(str(self.comment), f"{self.comment.id}.Test Comment...")


class ContactModelTest(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(
            name="Test User",
            email="test@example.com",
            subject="Test Subject",
            message="Test Message",
        )

    def test_contact_creation(self):
        self.assertEqual(self.contact.name, "Test User")
        self.assertEqual(self.contact.email, "test@example.com")
        self.assertEqual(self.contact.subject, "Test Subject")
        self.assertEqual(self.contact.message, "Test Message")


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Test Category")
        self.post = Post.objects.create(
            postname="Test Post",
            category=self.category,
            content="Test Content",
            user=self.user,
        )

    def test_index_view(self):
        self.client.login(username="testuser", password="password")
        with self.assertLogs("myapp.requests", level="INFO") as captured_logs:
            response = self.client.get("/?private=value")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertIn("X-Request-ID", response)
        self.assertIn("request_completed", captured_logs.output[0])
        self.assertNotIn("private=value", captured_logs.output[0])

    def test_blog_view(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get("/blog")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog.html")

    def test_create_view(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get("/create")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create.html")

    def test_free_materials_view(self):
        response = self.client.get("/free-materials")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "free-materials.html")
        self.assertContains(response, "Безкоштовні матеріали")
        self.assertContains(response, "free-english-guide.pdf")
        self.assertContains(response, "Home Alone")
        self.assertContains(response, "Bridgerton 1-4")
        self.assertContains(response, "Everyday Words")

    def test_schedule_view(self):
        response = self.client.get("/schedule")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "schedule.html")
        self.assertContains(response, "Графік роботи")

    def test_post_creation(self):
        self.client.login(username="testuser", password="password")
        response = self.client.post(
            "/create",
            {
                "postname": "New Post",
                "content": "New Content",
                "category": self.category.id,
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Post.objects.filter(postname="New Post").exists())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ContactRequestViewTest(TestCase):
    def test_contact_request_sends_uploaded_answer_file(self):
        answer_file = SimpleUploadedFile(
            "answers.pdf",
            b"test answers",
            content_type="application/pdf",
        )

        response = self.client.post(
            "/contact",
            {
                "name": "Student",
                "email": "student@example.com",
                "messenger": "@student",
                "message": "I want to improve speaking.",
                "answer_files": answer_file,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Відповіді надіслано")
        self.assertTrue(Contact.objects.filter(email="student@example.com").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0][0], "answers.pdf")

    @patch("myapp.views.EmailMessage.send", side_effect=RuntimeError("SMTP unavailable"))
    def test_contact_request_logs_email_delivery_failure(self, mocked_send):
        answer_file = SimpleUploadedFile(
            "answers.pdf",
            b"test answers",
            content_type="application/pdf",
        )

        with self.assertLogs("myapp.views", level="ERROR") as captured_logs:
            response = self.client.post(
                "/contact",
                {
                    "name": "Student",
                    "email": "student@example.com",
                    "answer_files": answer_file,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "лист не вдалося надіслати")
        self.assertTrue(Contact.objects.filter(email="student@example.com").exists())
        self.assertIn("contact_email_send_failed", captured_logs.output[0])
        mocked_send.assert_called_once_with(fail_silently=False)


class ReviewsRedirectTest(TestCase):
    @override_settings(INSTAGRAM_REVIEWS_URL="https://www.instagram.com/olena_khandii/")
    def test_reviews_redirects_to_instagram(self):
        response = self.client.get("/reviews")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://www.instagram.com/olena_khandii/")
