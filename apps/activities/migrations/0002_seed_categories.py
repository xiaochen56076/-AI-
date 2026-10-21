from django.db import migrations

CATEGORIES = [
    ("讲座学术", "lecture", "Reading", "#3B6BFA", 10),
    ("文艺演出", "art", "Microphone", "#8B5CF6", 20),
    ("体育竞技", "sports", "Trophy", "#F97316", 30),
    ("志愿服务", "volunteer", "Star", "#10B981", 40),
    ("社团招新", "recruitment", "Flag", "#EC4899", 50),
    ("创新创业", "innovation", "Promotion", "#0EA5E9", 60),
]

TAGS = [
    ("校级活动", "#3B6BFA"),
    ("志愿时长", "#10B981"),
    ("限量名额", "#F97316"),
    ("可加综测", "#8B5CF6"),
]


def seed(apps, schema_editor):
    Category = apps.get_model("activities", "ActivityCategory")
    Tag = apps.get_model("activities", "ActivityTag")
    for name, slug, icon, color, sort_order in CATEGORIES:
        Category.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "icon": icon,
                "color": color,
                "sort_order": sort_order,
                "is_active": True,
                "is_deleted": False,
            },
        )
    for name, color in TAGS:
        Tag.objects.update_or_create(
            name=name,
            defaults={"color": color, "is_active": True, "is_deleted": False},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
