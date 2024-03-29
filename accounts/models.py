from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class CustomAccountManager(BaseUserManager):

    def create_user(self, username, email, first_name, last_name, password=None):
        if not username:
            raise ValueError('username is required')
        if not email:
            raise ValueError('email is required')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name
        )

        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_superuser(self, username, email, first_name, last_name, password):
        user = self.create_user(username, email, first_name, last_name, password)

        user.is_admin = True
        user.is_staff = True
        user.is_superadmin = True
        user.is_active = True
        user.save(using=self.db)
        return user


class Account(AbstractBaseUser):
    username = models.CharField(max_length=50, blank=False, unique=True)
    email = models.EmailField(max_length=100, blank=False, unique=True)
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    phone_number = models.CharField(max_length=20)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = CustomAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, _):
        return self.is_admin

    def has_module_perms(self, _):
        return True


class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return str(self.user)

    def full_address(self):
        return f'{self.address_line1} {self.address_line2}'