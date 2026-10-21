from django.db import migrations

PERMISSIONS = [
    ("activity:create", "创建活动", "activity", "create"),
    ("activity:manage", "管理活动", "activity", "manage"),
    ("activity:audit", "审核活动", "activity", "audit"),
    ("signup:manage", "管理报名", "signup", "manage"),
    ("checkin:manage", "管理签到", "checkin", "manage"),
    ("analytics:activity", "查看活动数据", "analytics", "activity"),
    ("analytics:global", "查看全站数据", "analytics", "global"),
    ("user:manage", "管理用户", "user", "manage"),
    ("dict:manage", "维护字典", "dictionary", "manage"),
]

ROLES = {
    "STUDENT": {
        "name": "学生",
        "description": "浏览活动、报名、签到与接收通知",
        "permissions": [],
    },
    "ORGANIZER": {
        "name": "主办方",
        "description": "发布活动、管理报名与现场签到",
        "permissions": [
            "activity:create",
            "activity:manage",
            "signup:manage",
            "checkin:manage",
            "analytics:activity",
        ],
    },
    "AUDITOR": {
        "name": "审核员",
        "description": "审核活动内容与处理异常",
        "permissions": ["activity:audit"],
    },
    "ADMIN": {
        "name": "管理员",
        "description": "用户、字典与全站数据管理",
        "permissions": [item[0] for item in PERMISSIONS],
    },
}


def seed(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")

    permission_map = {}
    for codename, name, resource, action in PERMISSIONS:
        permission, _ = Permission.objects.update_or_create(
            codename=codename,
            defaults={"name": name, "resource": resource, "action": action},
        )
        permission_map[codename] = permission

    for code, config in ROLES.items():
        role, _ = Role.objects.update_or_create(
            code=code,
            defaults={"name": config["name"], "description": config["description"], "is_active": True},
        )
        for codename in config["permissions"]:
            RolePermission.objects.get_or_create(role=role, permission=permission_map[codename])


def unseed(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Permission = apps.get_model("accounts", "Permission")
    Role.objects.filter(code__in=ROLES).delete()
    Permission.objects.filter(codename__in=[item[0] for item in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
