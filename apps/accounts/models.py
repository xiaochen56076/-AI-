from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class Role(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(
        "Permission", through="RolePermission", related_name="roles", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sys_role"
        ordering = ["id"]

    def __str__(self):
        return f"{self.name}({self.code})"


class Permission(models.Model):
    codename = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    resource = models.CharField(max_length=32)
    action = models.CharField(max_length=32)

    class Meta:
        db_table = "sys_permission"
        ordering = ["codename"]

    def __str__(self):
        return self.codename


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "sys_role_permission"
        unique_together = ("role", "permission")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, student_no, password, **extra_fields):
        if not student_no:
            raise ValueError("学号不能为空")
        student_no = student_no.strip()
        user = self.model(student_no=student_no, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, student_no, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(student_no, password, **extra_fields)

    def create_superuser(self, student_no, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", User.Status.NORMAL)
        user = self._create_user(student_no, password, **extra_fields)
        admin_role = Role.objects.filter(code=User.RoleCode.ADMIN).first()
        if admin_role:
            user.roles.add(admin_role)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    class RoleCode(models.TextChoices):
        STUDENT = "STUDENT", "学生"
        ORGANIZER = "ORGANIZER", "主办方"
        AUDITOR = "AUDITOR", "审核员"
        ADMIN = "ADMIN", "管理员"

    class Status(models.IntegerChoices):
        NORMAL = 0, "正常"
        DISABLED = 1, "已禁用"

    student_no = models.CharField(max_length=20, unique=True)
    real_name = models.CharField(max_length=50)
    nickname = models.CharField(max_length=50, blank=True, default="")
    avatar_url = models.URLField(max_length=255, blank=True, default="")
    email = models.EmailField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    college = models.CharField(max_length=100, blank=True, default="")
    major = models.CharField(max_length=100, blank=True, default="")
    grade = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.SmallIntegerField(choices=Status.choices, default=Status.NORMAL)
    roles = models.ManyToManyField(Role, through="UserRole", related_name="users", blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "student_no"
    REQUIRED_FIELDS = ["real_name"]

    objects = UserManager()

    class Meta:
        db_table = "sys_user"
        indexes = [models.Index(fields=["college", "major"], name="idx_college_major")]

    @property
    def is_active(self):
        return self.status == self.Status.NORMAL and not self.is_deleted

    @property
    def display_name(self):
        return self.nickname or self.real_name or self.student_no

    def has_role(self, code: str) -> bool:
        return self.roles.filter(code=code, is_active=True).exists()

    def permission_codenames(self) -> set[str]:
        if self.is_superuser:
            return set(Permission.objects.values_list("codename", flat=True))
        return set(
            Permission.objects.filter(roles__users=self, roles__is_active=True).values_list(
                "codename", flat=True
            )
        )

    def get_full_name(self):
        return self.real_name

    def get_short_name(self):
        return self.nickname or self.real_name

    def __str__(self):
        return f"{self.real_name}({self.student_no})"


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sys_user_role"
        unique_together = ("user", "role")
