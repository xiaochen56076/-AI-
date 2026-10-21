from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.activities.models import (
    Activity,
    ActivityCategory,
    ActivityTag,
    AuditRecord,
    Favorite,
)
from apps.clubs.models import Club
from apps.notifications.models import Notification
from apps.notifications.services import (
    notify,
    notify_activity_cancelled,
    notify_activity_reminders,
    notify_checkin_success,
)
from apps.signups.models import CheckinRecord, Signup
from apps.signups.services import signup_for_activity

PASSWORD = "Campushub@2026"

CATEGORIES = [
    ("lecture", "学术讲座", "Microphone", "#3757e8", 10),
    ("art", "文艺演出", "Film", "#7a5af8", 20),
    ("sports", "体育竞技", "Basketball", "#0ea5e9", 30),
    ("volunteer", "志愿服务", "Flag", "#0f9f6e", 40),
    ("recruitment", "社团招新", "Promotion", "#f97316", 50),
    ("innovation", "创新创业", "Present", "#0ea5e9", 60),
    ("career", "就业创业", "Reading", "#d98a00", 70),
    ("life", "生活休闲", "Coffee", "#ec4899", 80),
    ("contest", "科创竞赛", "Trophy", "#0f766e", 90),
]

DEMO_ONLY_CATEGORIES = ("career", "life", "contest", "closed")

TAGS = [
    ("新生友好", "#3757e8"),
    ("免费参与", "#0f9f6e"),
    ("第二课堂学分", "#d98a00"),
    ("热门", "#e0484b"),
    ("周末", "#7a5af8"),
    ("需要面试", "#0ea5e9"),
    ("颁发证书", "#64748b"),
    ("名额紧张", "#f97316"),
    ("可带朋友", "#ec4899"),
    ("线上参与", "#14b8a6"),
    ("夜间", "#4f46e5"),
    ("期末", "#b45309"),
]

STAFF = [
    ("20210001", "陈书宁", "学生工作部信息中心", "平台运维", ["ADMIN"]),
    ("20190001", "沈砚清", "校团委", "活动审核", ["AUDITOR", "STUDENT"]),
]

ORGANIZERS = [
    ("20220101", "林可夷", "计算机学院", "软件工程", 3, "代码造物社"),
    ("20220102", "周亦然", "地球科学与工程学院", "地质学", 4, "星空天文社"),
    ("20220103", "苏与白", "文学院", "汉语言文学", 2, "校园文化生活社"),
]

STUDENT_NAMES = [
    ("赵叙白", "计算机学院", "人工智能", 2023),
    ("钱知遥", "电子信息学院", "通信工程", 2022),
    ("孙嘉树", "机械工程学院", "机械设计", 2024),
    ("李慕清", "外国语学院", "英语", 2023),
    ("周雨砚", "建筑学院", "城乡规划", 2022),
    ("吴见山", "数学学院", "应用数学", 2024),
    ("郑幼薇", "化学学院", "高分子材料", 2023),
    ("王砚舟", "土木学院", "桥梁工程", 2021),
    ("冯落言", "艺术学院", "视觉传达", 2024),
    ("陈叙微", "新闻传播学院", "网络与新媒体", 2022),
    ("褚叶青", "生命科学学院", "生物技术", 2023),
    ("卫清和", "经济学院", "金融学", 2021),
    ("蒋知微", "医学院", "临床医学", 2022),
    ("沈砚舟", "法学院", "法学", 2024),
    ("韩牧之", "计算机学院", "网络空间安全", 2023),
    ("杨溯流", "环境学院", "环境科学", 2021),
    ("朱照野", "体育部", "运动训练", 2022),
    ("秦揽月", "外国语学院", "日语", 2024),
]


def at(days=0, hour=9, minute=0):
    return timezone.localtime(timezone.now()).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    ) + timezone.timedelta(days=days)


ACTIVITIES = [
    {
        "key": "hackathon",
        "title": "新生编程马拉松：48 小时造点东西",
        "category": "contest",
        "organizer": 0,
        "summary": "组队完成一个能跑起来的校园小工具，导师全程陪跑，优秀项目直通省级赛事。",
        "description": (
            "面向全校本科生的 48 小时创作营。现场按方向分组：校园服务、学习效率、公益可视化。\n\n"
            "· 开营：需求梳理与组队（第 1 小时）\n"
            "· 中段：三位企业导师轮巡答疑\n"
            "· 结营：6 分钟路演 + 现场评审\n\n"
            "电脑、电源、白板笔由主办方提供，请自带充电器与一颗愿意折腾的心。"
        ),
        "location": "图书馆 B1 创客空间",
        "start": at(6, 9),
        "end": at(8, 21),
        "signup_start": at(-2, 9),
        "signup_end": at(5, 12),
        "capacity": 120,
        "waitlist": 30,
        "checkin_mode": 2,
        "status": Activity.Status.PUBLISHED,
        "tags": ["新生友好", "热门", "颁发证书"],
        "views": 1863,
        "signups": 9,
    },
    {
        "key": "folk",
        "title": "校园民谣夜 · 秋声专场",
        "category": "art",
        "organizer": 2,
        "summary": "六组学生音乐人，木吉他与手风琴，把秋天唱给你听。",
        "description": (
            "露天小剧场形式的民谣演出，节目单已确认：原创 4 首、改编 2 首、返场合唱 1 首。\n\n"
            "入场可自带野餐垫，请勿携带玻璃容器。演出约 100 分钟，中途有一次换场休息。"
        ),
        "location": "北校区草坪剧场",
        "start": at(3, 19),
        "end": at(3, 21),
        "signup_start": at(-5, 10),
        "signup_end": at(3, 17),
        "capacity": 300,
        "waitlist": 0,
        "checkin_mode": 1,
        "status": Activity.Status.PUBLISHED,
        "tags": ["免费参与", "周末", "可带朋友"],
        "views": 2431,
        "signups": 6,
    },
    {
        "key": "llm-lecture",
        "title": "AI 通识公开课：大模型会怎样改变你的学习",
        "category": "lecture",
        "organizer": 0,
        "summary": "不讲公式只讲用法，现场演示用大模型读文献、写综述、备考复习。",
        "description": (
            "本场公开课面向所有专业，重点回答三个问题：\n\n"
            "1. 什么样的任务适合交给模型，什么样的必须自己做；\n"
            "2. 如何提问才能得到可用的结果；\n"
            "3. 学术诚信边界在哪里。\n\n"
            "讲后留 20 分钟自由提问，可带电脑跟练。"
        ),
        "location": "主教学楼 A201",
        "start": at(2, 14, 30),
        "end": at(2, 16, 30),
        "signup_start": at(-3, 8),
        "signup_end": at(2, 12),
        "capacity": 200,
        "waitlist": 50,
        "checkin_mode": 2,
        "status": Activity.Status.PUBLISHED,
        "tags": ["热门", "第二课堂学分", "新生友好"],
        "views": 3120,
        "signups": 8,
    },
    {
        "key": "beach",
        "title": "周末红树林净滩志愿行动",
        "category": "volunteer",
        "organizer": 1,
        "summary": "大巴往返，捡拾与记录并重，志愿服务时长如实计入。",
        "description": (
            "与本地环保组织共同开展的净滩行动，分组负责不同岸段的清理与垃圾计数。\n\n"
            "统一发放手套、夹钳与记录表；请在集合点完成签到，中途离场需向组长报备。"
            "净滩数据会汇总进季度报告。"
        ),
        "location": "南门大巴集合点 → 湾东红树林",
        "start": at(5, 7, 30),
        "end": at(5, 16),
        "signup_start": at(-6, 9),
        "signup_end": at(4, 18),
        "capacity": 40,
        "waitlist": 20,
        "checkin_mode": 2,
        "status": Activity.Status.PUBLISHED,
        "tags": ["周末", "颁发证书", "名额紧张"],
        "views": 942,
        "signups": 5,
    },
    {
        "key": "basketball",
        "title": "三人制篮球班级联赛 · 小组赛",
        "category": "sports",
        "organizer": 0,
        "summary": "以班级为单位报名，每队 3-4 人，裁判与计时由体育学院同学担任。",
        "description": "小组赛共 4 片场地同时进行，采用上下半场各 10 分钟的计时规则。"
        "请穿着运动鞋，自备饮用水。赛程表将在开赛前一天于活动现场公布。",
        "location": "西体育馆 2 号篮球场",
        "start": at(4, 15),
        "end": at(4, 19),
        "signup_start": at(-4, 9),
        "signup_end": at(3, 20),
        "capacity": 64,
        "waitlist": 0,
        "checkin_mode": 2,
        "status": Activity.Status.PUBLISHED,
        "tags": ["周末", "热门"],
        "views": 1275,
        "signups": 4,
    },
    {
        "key": "resume",
        "title": "简历诊所：HR 面对面改简历",
        "category": "career",
        "organizer": 2,
        "summary": "6 位企业 HR 轮值，一人一档，现场逐段修改，名额极少。",
        "description": (
            "每位同学有 20 分钟的一对一时间，请提前把简历打印一份带来。\n\n"
            "现场按报名顺序叫号，迟到 10 分钟视为放弃本轮，可顺延至下一位之后。"
        ),
        "location": "学生活动中心 305 室",
        "start": at(2, 18),
        "end": at(2, 21),
        "signup_start": at(-1, 9),
        "signup_end": at(2, 17),
        "capacity": 6,
        "waitlist": 10,
        "checkin_mode": 1,
        "status": Activity.Status.PUBLISHED,
        "tags": ["名额紧张", "需要面试"],
        "views": 1560,
        "signups": 9,
    },
    {
        "key": "coffee",
        "title": "手冲咖啡入门工作坊",
        "category": "life",
        "organizer": 2,
        "summary": "从研磨度到水温，一人一套器具，冲完自己喝。",
        "description": "小班级教学，12 人为上限。包含三种豆子的对比杯测，全程约 90 分钟。"
        "对咖啡因敏感的同学可换成路易波士茶。",
        "location": "生活园区 3 栋咖啡吧",
        "start": at(7, 14),
        "end": at(7, 16),
        "signup_start": at(-1, 10),
        "signup_end": at(6, 20),
        "capacity": 16,
        "waitlist": 0,
        "checkin_mode": 1,
        "status": Activity.Status.PUBLISHED,
        "tags": ["新生友好", "周末"],
        "views": 688,
        "signups": 3,
    },
    {
        "key": "debate",
        "title": "辩论社春季招新宣讲",
        "category": "recruitment",
        "organizer": 1,
        "summary": "报名尚未开始，先收藏，开抢当天会有提醒。",
        "description": "宣讲包含一支表演赛、赛制讲解与面试官答疑。招新面试分两天进行，"
        "不限专业，不需要基础。",
        "location": "人文楼 B103",
        "start": at(12, 19),
        "end": at(12, 20, 30),
        "signup_start": at(1, 10),
        "signup_end": at(11, 12),
        "capacity": 150,
        "waitlist": 0,
        "checkin_mode": 2,
        "status": Activity.Status.PUBLISHED,
        "tags": ["需要面试", "新生友好"],
        "views": 320,
        "signups": 0,
    },
    {
        "key": "meteor",
        "title": "英仙座流星雨夜观行动",
        "category": "contest",
        "organizer": 1,
        "summary": "待审核：光污染较低的观测点，望远镜 6 台轮流使用。",
        "description": "活动含望远镜使用培训、流星计数记录与凌晨的观星分享环节。"
        "如遇阴雨将改期并在平台发布通知。",
        "location": "象鼻山观测点（包车往返）",
        "start": at(15, 21),
        "end": at(16, 3),
        "signup_start": at(1, 9),
        "signup_end": at(14, 18),
        "capacity": 50,
        "waitlist": 10,
        "checkin_mode": 2,
        "status": Activity.Status.PENDING,
        "tags": ["夜间", "名额紧张"],
        "views": 40,
        "signups": 0,
        "audit": None,
    },
    {
        "key": "first-aid",
        "title": "校园急救技能实训",
        "category": "volunteer",
        "organizer": 0,
        "summary": "待审核：心肺复苏与 AED 使用实操，通过考核发放结业卡。",
        "description": "由校医院医生带队，人手一具模拟人，重点练习胸外按压节奏、"
        "海姆立克急救法与 AED 电极片位置。",
        "location": "校医院技能训练室",
        "start": at(9, 14),
        "end": at(9, 17),
        "signup_start": at(1, 8),
        "signup_end": at(8, 12),
        "capacity": 30,
        "waitlist": 0,
        "checkin_mode": 2,
        "status": Activity.Status.PENDING,
        "tags": ["颁发证书", "第二课堂学分"],
        "views": 26,
        "signups": 0,
        "audit": None,
    },
    {
        "key": "gamedev",
        "title": "独立游戏开发分享会",
        "category": "innovation",
        "organizer": 2,
        "summary": "待审核：三位在校生开发者分享从原型到上架的全过程。",
        "description": "包含美术成本取舍、试玩反馈收集与发行平台选择三段内容，"
        "现场提供两台试玩机。",
        "location": "创新中心路演厅",
        "start": at(10, 19),
        "end": at(10, 21),
        "signup_start": at(2, 9),
        "signup_end": at(9, 18),
        "capacity": 80,
        "waitlist": 20,
        "checkin_mode": 2,
        "status": Activity.Status.PENDING,
        "tags": ["热门"],
        "views": 55,
        "signups": 0,
        "audit": None,
    },
    {
        "key": "study-room",
        "title": "期末自习室加座计划",
        "category": "life",
        "organizer": 0,
        "summary": "草稿：还在确认哪几间教室可以在夜间开放。",
        "description": "计划在期末周增设 120 个自习座位，并延长两间研讨室开放时间。"
        "具体楼层与预约方式待定。",
        "location": "图书馆 3-5 层",
        "start": at(18, 8),
        "end": at(25, 23),
        "signup_start": at(4, 9),
        "signup_end": at(17, 22),
        "capacity": 120,
        "waitlist": 0,
        "checkin_mode": 0,
        "status": Activity.Status.DRAFT,
        "tags": ["期末"],
        "views": 8,
        "signups": 0,
    },
    {
        "key": "photo-walk",
        "title": "摄影外拍：城市光影",
        "category": "life",
        "organizer": 2,
        "summary": "草稿：路线还没最终确定，先记下想法。",
        "description": "傍晚出发，走老街与码头两条线路，结束后来一场小范围选片讨论。"
        "设备不限，手机也可以参加。",
        "location": "东门集合 → 老城码头",
        "start": at(20, 17),
        "end": at(20, 21),
        "signup_start": at(6, 10),
        "signup_end": at(19, 18),
        "capacity": 25,
        "waitlist": 0,
        "checkin_mode": 1,
        "status": Activity.Status.DRAFT,
        "tags": ["可带朋友"],
        "views": 5,
        "signups": 0,
    },
    {
        "key": "bbq",
        "title": "深夜食堂：宿舍楼下的烧烤局",
        "category": "life",
        "organizer": 2,
        "summary": "已驳回：场地与安全预案说明不足。",
        "description": "计划在宿舍区空地组织小型烧烤聚会，需补充消防与用电方案后重新提交。",
        "location": "生活园区 5 栋空地",
        "start": at(11, 19),
        "end": at(11, 22),
        "signup_start": at(3, 9),
        "signup_end": at(10, 20),
        "capacity": 40,
        "waitlist": 0,
        "checkin_mode": 0,
        "status": Activity.Status.REJECTED,
        "tags": ["夜间"],
        "views": 90,
        "signups": 0,
        "audit": (
            AuditRecord.Action.REJECT,
            "宿舍区明火烧烤不符合校园消防规定，请补充场地审批与安全预案后重新提交。",
        ),
    },
    {
        "key": "orienteering",
        "title": "开学季校园定向越野",
        "category": "sports",
        "organizer": 0,
        "summary": "已结束：12 个打卡点，最快完赛 41 分钟。",
        "description": "以 3 人小队形式完成校园 12 个点位打卡，兼具趣味问答任务。"
        "完赛队伍均可领取纪念徽章。",
        "location": "全校园区",
        "start": at(-12, 8),
        "end": at(-12, 12),
        "signup_start": at(-25, 9),
        "signup_end": at(-13, 20),
        "capacity": 90,
        "waitlist": 0,
        "checkin_mode": 2,
        "status": Activity.Status.ENDED,
        "tags": ["新生友好", "颁发证书"],
        "views": 2050,
        "attendance": (12, 9, 2, 1),
    },
    {
        "key": "city-lecture",
        "title": "名师讲堂：如何读一座城市",
        "category": "lecture",
        "organizer": 1,
        "summary": "已结束：历史地理方向的通识讲座，现场提问很热烈。",
        "description": "从街名、河道与老地图切入，讲一种观察城市的方法。"
        "讲后书单已在平台置顶。",
        "location": "图书馆报告厅",
        "start": at(-8, 14, 30),
        "end": at(-8, 16, 30),
        "signup_start": at(-18, 9),
        "signup_end": at(-9, 12),
        "capacity": 180,
        "waitlist": 0,
        "checkin_mode": 2,
        "status": Activity.Status.ENDED,
        "tags": ["第二课堂学分", "热门"],
        "views": 1740,
        "attendance": (10, 8, 2, 0),
    },
    {
        "key": "club-fair",
        "title": "社团嘉年华秋季市集",
        "category": "recruitment",
        "organizer": 2,
        "summary": "已结束：48 个社团摆摊招新，现场面试 300 余人次。",
        "description": "两天市集，舞台每 30 分钟一轮社团展演，各社团在固定摊位接受报名表。",
        "location": "中心广场",
        "start": at(-20, 10),
        "end": at(-20, 18),
        "signup_start": at(-32, 9),
        "signup_end": at(-21, 20),
        "capacity": 500,
        "waitlist": 0,
        "checkin_mode": 1,
        "status": Activity.Status.ENDED,
        "tags": ["周末", "可带朋友"],
        "views": 3980,
        "attendance": (14, 11, 3, 0),
    },
    {
        "key": "mindfulness",
        "title": "心理健康月：正念减压工作坊",
        "category": "life",
        "organizer": 1,
        "summary": "已结束：40 分钟呼吸练习加团体讨论。",
        "description": "由心理咨询中心老师带领，练习身体扫描与呼吸锚定，"
        "结束后提供一对一咨询预约通道。",
        "location": "学生活动中心 201 团辅室",
        "start": at(-5, 19),
        "end": at(-5, 20, 30),
        "signup_start": at(-14, 9),
        "signup_end": at(-6, 18),
        "capacity": 24,
        "waitlist": 0,
        "checkin_mode": 0,
        "status": Activity.Status.ENDED,
        "tags": ["名额紧张"],
        "views": 760,
        "attendance": (8, 8, 0, 0),
    },
    {
        "key": "open-air-film",
        "title": "露天电影夜：雨中即景",
        "category": "art",
        "organizer": 2,
        "summary": "已取消：设备受潮，当晚无法放映。",
        "description": "原定放映两部学生短片与一部故事片，因放映设备受潮取消，"
        "已报名同学无需操作。",
        "location": "南草坪",
        "start": at(-3, 19, 30),
        "end": at(-3, 22),
        "signup_start": at(-10, 9),
        "signup_end": at(-4, 18),
        "capacity": 200,
        "waitlist": 0,
        "checkin_mode": 1,
        "status": Activity.Status.CANCELLED,
        "tags": ["夜间", "周末"],
        "views": 1180,
        "attendance": (6, 0, 0, 0),
        "cancel_reason": "放映设备受雨受潮，无法保证观影效果与安全，活动取消，后续改期另行通知。",
    },
]


class Command(BaseCommand):
    help = "写入一套可浏览、可报名、可签到、可审核的演示数据"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="先清空演示数据再写入")
        parser.add_argument("--purge", action="store_true", help="只清空演示数据，不写入")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"] or options["purge"]:
            removed = self._purge()
            self.stdout.write(self.style.WARNING(f"已清理演示数据：{removed} 个活动及相关记录"))
        if options["purge"]:
            return
        if Activity.objects.filter(title__in=[item["title"] for item in ACTIVITIES]).exists():
            raise CommandError("演示数据已存在，如需重建请使用 --reset")

        categories = self._seed_categories()
        tags = self._seed_tags()
        users = self._seed_users()
        created = self._seed_activities(users, categories, tags)
        self._seed_extras(users, created)

        self.stdout.write(
            self.style.SUCCESS(
                f"演示数据写入完成：{len(created)} 个活动、"
                f"{Signup.objects.count()} 条报名、{Notification.objects.count()} 条通知"
            )
        )
        self.stdout.write(f"统一登录密码：{PASSWORD}")
        accounts = [
            (STAFF[0][0], "管理员"),
            (STAFF[1][0], "审核员"),
            (ORGANIZERS[0][0], "主办方"),
            ("20220201", "学生"),
        ]
        for student_no, label in accounts:
            self.stdout.write(f"  {label}：{student_no}")

    def _purge(self):
        titles = [item["title"] for item in ACTIVITIES]
        activities = list(Activity.objects.filter(title__in=titles))
        ids = [item.pk for item in activities]
        Notification.objects.filter(activity_id__in=ids).update(activity=None)
        CheckinRecord.objects.filter(activity_id__in=ids).delete()
        Signup.objects.filter(activity_id__in=ids).delete()
        Favorite.objects.filter(activity_id__in=ids).delete()
        count = Activity.objects.filter(pk__in=ids).delete()[0]
        Club.objects.filter(name__in=[item[5] for item in ORGANIZERS]).delete()
        User.objects.filter(
            student_no__in=[item[0] for item in STAFF + ORGANIZERS]
            + [f"202202{i:02d}" for i in range(1, len(STUDENT_NAMES) + 1)]
        ).delete()
        ActivityTag.objects.filter(name__in=[item[0] for item in TAGS]).delete()
        ActivityCategory.objects.filter(slug__in=DEMO_ONLY_CATEGORIES).delete()
        return count

    def _seed_categories(self):
        result = {}
        for slug, name, icon, color, order in CATEGORIES:
            category, _ = ActivityCategory.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "icon": icon,
                    "color": color,
                    "sort_order": order,
                    "is_active": True,
                    "is_deleted": False,
                },
            )
            result[slug] = category
        result["unused"] = ActivityCategory.objects.update_or_create(
            slug="closed",
            defaults={
                "name": "已停用分类",
                "icon": "Star",
                "color": "#94a3b8",
                "sort_order": 990,
                "is_active": False,
            },
        )[0]
        return result

    def _seed_tags(self):
        result = {}
        for name, color in TAGS:
            result[name], _ = ActivityTag.objects.update_or_create(
                name=name, defaults={"color": color, "is_active": True}
            )
        return result

    def _seed_users(self):
        roles = {role.code: role for role in Role.objects.all()}
        student_nos = []

        def upsert(student_no, real_name, college, major, grade, role_codes):
            user, created = User.objects.get_or_create(
                student_no=student_no,
                defaults={
                    "real_name": real_name,
                    "nickname": real_name,
                    "college": college,
                    "major": major,
                    "grade": grade,
                    "status": User.Status.NORMAL,
                    "email": f"{student_no}@campus.edu.cn",
                },
            )
            user.set_password(PASSWORD)
            user.save(update_fields=["password", "updated_at"])
            user.roles.set([roles[code] for code in role_codes if code in roles])
            return user

        for student_no, name, college, duty, role_codes in STAFF:
            upsert(student_no, name, college, duty, 2019, role_codes)
        organizers = []
        for item in ORGANIZERS:
            organizers.append(
                upsert(item[0], item[1], item[2], item[3], item[4], ["ORGANIZER", "STUDENT"])
            )
        students = []
        for index, (name, college, major, grade) in enumerate(STUDENT_NAMES):
            student_no = f"202202{index + 1:02d}"
            student_nos.append(student_no)
            students.append(upsert(student_no, name, college, major, grade, ["STUDENT"]))
        return {"organizers": organizers, "students": students}

    def _seed_activities(self, users, categories, tags):
        created = {}
        for spec in ACTIVITIES:
            organizer = users["organizers"][spec["organizer"]]
            activity = Activity.objects.filter(title=spec["title"]).first()
            if activity is None:
                activity = Activity.objects.create(
                    organizer=organizer,
                    club=self._club(organizer),
                    category=categories[spec["category"]],
                    title=spec["title"],
                    summary=spec["summary"],
                    description=spec["description"],
                    location=spec["location"],
                    start_time=spec["start"],
                    end_time=spec["end"],
                    signup_start=spec["signup_start"],
                    signup_end=spec["signup_end"],
                    capacity=spec["capacity"],
                    waitlist_enabled=bool(spec["waitlist"]),
                    waitlist_limit=spec["waitlist"],
                    checkin_mode=spec["checkin_mode"],
                    status=spec["status"],
                    cancel_reason=spec.get("cancel_reason", ""),
                    view_count=spec["views"],
                )
            else:
                Activity.objects.filter(pk=activity.pk).update(
                    status=spec["status"], view_count=spec["views"], is_deleted=False
                )
                activity.refresh_from_db()
            activity.tags.set([tags[name] for name in spec["tags"] if name in tags])
            self._audit_trail(activity, users, spec)
            created[spec["key"]] = activity
        self._fill_registrations(created, users)
        return created

    def _club(self, organizer):
        spec = next(item for item in ORGANIZERS if item[0] == organizer.student_no)
        club, _ = Club.objects.update_or_create(
            name=spec[5],
            defaults={
                "description": f"{spec[2]}·{spec[1]}负责的学生组织，长期在校内开展活动。",
                "owner": organizer,
                "is_active": True,
                "is_deleted": False,
            },
        )
        return club

    def _audit_trail(self, activity, users, spec):
        AuditRecord.objects.filter(activity=activity).delete()
        auditor = User.objects.filter(student_no=STAFF[1][0]).first()
        if not auditor:
            return
        if spec["status"] in {Activity.Status.PUBLISHED, Activity.Status.CANCELLED}:
            AuditRecord.objects.create(
                activity=activity,
                auditor=auditor,
                action=AuditRecord.Action.APPROVE,
                comment="信息完整，时间与场地安排合理，通过发布。",
            )
        elif spec.get("audit"):
            action, comment = spec["audit"]
            AuditRecord.objects.create(
                activity=activity, auditor=auditor, action=action, comment=comment
            )
        if spec["status"] == Activity.Status.REJECTED:
            notify(
                activity.organizer,
                Notification.Type.ACTIVITY_AUDITED,
                "活动审核未通过",
                f"你的活动《{activity.title}》未通过审核。审核意见：{spec['audit'][1]}",
                activity,
            )

    def _fill_registrations(self, created, users):
        students = users["students"]
        for spec in ACTIVITIES:
            activity = created[spec["key"]]
            count = spec.get("signups", 0)
            if activity.status == Activity.Status.PUBLISHED and count:
                pool = [students[index % len(students)] for index in range(count)]
                for offset, student in enumerate(pool):
                    signup, _ = signup_for_activity(activity.pk, student, remark="")
                    Signup.objects.filter(pk=signup.pk).update(
                        signup_at=min(
                            activity.signup_start + timezone.timedelta(
                                hours=offset * 3, minutes=offset * 11
                            ),
                            timezone.now(),
                        )
                    )
            attendance = spec.get("attendance")
            if attendance:
                self._fill_attendance(activity, students, attendance, spec)

    def _fill_attendance(self, activity, students, attendance, spec):
        total, present, absent, manual = attendance
        reason = spec.get("cancel_reason", "")
        for offset in range(min(total, len(students))):
            student = students[offset % len(students)]
            if activity.status == Activity.Status.CANCELLED:
                Signup.objects.create(
                    activity=activity,
                    user=student,
                    status=Signup.Status.CANCELLED,
                    remark=reason[:255],
                    cancel_at=activity.start_time - timezone.timedelta(hours=2),
                    signup_at=activity.signup_start + timezone.timedelta(hours=offset),
                )
                continue
            status = (
                Signup.Status.SUCCESS
                if activity.checkin_mode == Activity.CheckinMode.NONE
                else (Signup.Status.CHECKED_IN if offset < present else Signup.Status.NO_SHOW)
            )
            signup = Signup.objects.create(
                activity=activity,
                user=student,
                status=status,
                signup_at=activity.signup_start + timezone.timedelta(hours=offset),
            )
            if status == Signup.Status.CHECKED_IN:
                record = CheckinRecord.objects.create(
                    signup=signup,
                    activity=activity,
                    user=student,
                    method=CheckinRecord.Method.MANUAL if offset >= present - manual else CheckinRecord.Method.SCAN,
                    reason="现场手机没电，由主办方补签" if offset >= present - manual else "",
                    operator=activity.organizer if offset >= present - manual else None,
                    checkin_at=activity.start_time
                    + timezone.timedelta(minutes=4 + offset * 3),
                    device_info="CampusHub Web" if offset < present - manual else "",
                )
                if offset < 3:
                    notify_checkin_success(record)
        counts = Signup.objects.filter(activity=activity).values_list("status", flat=True)
        success = len([item for item in counts if item == Signup.Status.SUCCESS])
        checked = len([item for item in counts if item == Signup.Status.CHECKED_IN])
        no_show = len([item for item in counts if item == Signup.Status.NO_SHOW])
        Activity.objects.filter(pk=activity.pk).update(signup_count=success + checked + no_show)
        if activity.status == Activity.Status.CANCELLED:
            notify_activity_cancelled(
                activity, reason, [item.user_id for item in Signup.objects.filter(activity=activity)]
            )

    def _seed_extras(self, users, created):
        students = users["students"]
        for spec in ACTIVITIES:
            activity = created[spec["key"]]
            if spec["status"] != Activity.Status.PUBLISHED:
                continue
            signed = list(Signup.objects.filter(activity=activity).select_related("user"))
            if signed and spec["start"] > timezone.now():
                notify_activity_reminders(activity, [item.user_id for item in signed[:4]])
        for key in ("hackathon", "city-lecture", "club-fair"):
            activity = created.get(key)
            if activity:
                Favorite.objects.get_or_create(user=students[0], activity=activity)
                Favorite.objects.get_or_create(user=students[3], activity=activity)
        notify(
            students[0],
            Notification.Type.SYSTEM,
            "欢迎使用 CampusHub",
            "校园活动平台已上线，可在活动广场浏览、报名并使用二维码签到。"
            "演示账号统一密码为 " + PASSWORD + "。",
        )
