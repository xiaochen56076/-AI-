from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status

from apps.accounts.models import User
from apps.clubs.models import Club
from apps.notifications.services import notify_audit_result
from common.exceptions import BusinessError
from common.permissions import user_has_permission

from .models import Activity, ActivityTagRel, AuditRecord, Favorite

MANAGEABLE_FIELDS = {
    "summary",
    "description",
    "cover_url",
    "tags",
}


def can_manage_activity(user, activity: Activity) -> bool:
    return bool(user and user.is_authenticated and activity.organizer_id == user.id)


def can_admin_manage(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_superuser
            or user.roles.filter(code=User.RoleCode.ADMIN, is_active=True).exists()
        )
    )


def ensure_owner(user, activity: Activity):
    if not can_manage_activity(user, activity):
        raise BusinessError("只能管理自己发布的活动", 30002, status.HTTP_403_FORBIDDEN)


def assert_activity_state(activity: Activity, allowed: set[int], message: str):
    if activity.status not in allowed:
        raise BusinessError(message, 30001, status.HTTP_409_CONFLICT)


def resolve_club(organizer, club: Club | None) -> Club:
    if club is not None:
        if club.owner_id != organizer.id:
            raise BusinessError("不能使用其他主办方的社团", 30002, status.HTTP_403_FORBIDDEN)
        return club
    owned = Club.objects.filter(owner=organizer, is_active=True, is_deleted=False).first()
    if owned:
        return owned
    default_name = f"{organizer.display_name}的活动社"[:100]
    return Club.objects.create(
        name=default_name,
        description="由 CampusHub 自动创建的主办方空间",
        owner=organizer,
    )


@transaction.atomic
def create_activity(organizer, validated_data: dict) -> Activity:
    tags = validated_data.pop("tags", [])
    club = resolve_club(organizer, validated_data.pop("club", None))
    activity = Activity.objects.create(
        organizer=organizer,
        club=club,
        status=Activity.Status.DRAFT,
        **validated_data,
    )
    _replace_tags(activity, tags)
    return activity


def _replace_tags(activity: Activity, tags):
    ActivityTagRel.objects.filter(activity=activity).delete()
    ActivityTagRel.objects.bulk_create([ActivityTagRel(activity=activity, tag=tag) for tag in tags])


@transaction.atomic
def update_activity(activity_id: int, user, validated_data: dict) -> Activity:
    activity = Activity.objects.select_for_update().filter(pk=activity_id, is_deleted=False).first()
    if not activity:
        raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
    ensure_owner(user, activity)
    assert_activity_state(
        activity,
        {Activity.Status.DRAFT, Activity.Status.REJECTED, Activity.Status.PUBLISHED},
        "当前状态不支持编辑",
    )
    if activity.status == Activity.Status.PUBLISHED:
        forbidden = set(validated_data) - MANAGEABLE_FIELDS
        if forbidden:
            raise BusinessError(
                "已发布活动只能修改简介、详情、封面和标签，关键信息请取消后重新发布",
                30001,
                status.HTTP_409_CONFLICT,
            )
    if "club" in validated_data and validated_data["club"].owner_id != user.id:
        raise BusinessError("不能使用其他主办方的社团", 30002, status.HTTP_403_FORBIDDEN)

    tags = validated_data.pop("tags", None)
    for field, value in validated_data.items():
        setattr(activity, field, value)
    activity.save()
    if tags is not None:
        _replace_tags(activity, tags)
    return activity


@transaction.atomic
def submit_activity(activity_id: int, user) -> Activity:
    activity = Activity.objects.select_for_update().filter(pk=activity_id, is_deleted=False).first()
    if not activity:
        raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
    ensure_owner(user, activity)
    assert_activity_state(
        activity,
        {Activity.Status.DRAFT, Activity.Status.REJECTED},
        "只有草稿或已驳回活动可以提交审核",
    )
    if activity.start_time <= timezone.now():
        raise BusinessError("活动开始时间已过，请先调整时间", 30003, status.HTTP_409_CONFLICT)
    if not activity.category.is_active:
        raise BusinessError("活动分类已停用，请重新选择分类", 30003, status.HTTP_409_CONFLICT)
    activity.status = Activity.Status.PENDING
    activity.cancel_reason = ""
    activity.save(update_fields=["status", "cancel_reason", "updated_at"])
    return activity


@transaction.atomic
def review_activity(activity_id: int, auditor, action: int, comment: str) -> Activity:
    activity = Activity.objects.select_for_update().filter(pk=activity_id, is_deleted=False).first()
    if not activity:
        raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
    if activity.status != Activity.Status.PENDING:
        raise BusinessError("该活动已被处理，请刷新列表", 30005, status.HTTP_409_CONFLICT)
    if action not in {AuditRecord.Action.APPROVE, AuditRecord.Action.REJECT}:
        raise BusinessError("无效的审核动作", 30006, status.HTTP_400_BAD_REQUEST)
    if action == AuditRecord.Action.REJECT and not comment.strip():
        raise BusinessError("驳回活动时必须填写审核意见", 30007, status.HTTP_400_BAD_REQUEST)

    activity.status = (
        Activity.Status.PUBLISHED
        if action == AuditRecord.Action.APPROVE
        else Activity.Status.REJECTED
    )
    activity.save(update_fields=["status", "updated_at"])
    AuditRecord.objects.create(
        activity=activity,
        auditor=auditor,
        action=action,
        comment=comment.strip(),
    )
    notify_audit_result(
        activity, approved=action == AuditRecord.Action.APPROVE, comment=comment
    )
    return activity


@transaction.atomic
def cancel_activity(activity_id: int, user, reason: str = "") -> Activity:
    activity = Activity.objects.select_for_update().filter(pk=activity_id, is_deleted=False).first()
    if not activity:
        raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
    if not (can_manage_activity(user, activity) or can_admin_manage(user)):
        raise BusinessError("只能取消自己发布的活动", 30002, status.HTTP_403_FORBIDDEN)
    assert_activity_state(
        activity,
        {
            Activity.Status.DRAFT,
            Activity.Status.PENDING,
            Activity.Status.PUBLISHED,
            Activity.Status.REJECTED,
        },
        "活动已结束或已取消",
    )
    if (
        activity.status in {Activity.Status.PUBLISHED, Activity.Status.PENDING}
        and not reason.strip()
    ):
        raise BusinessError("下架活动需要填写原因", 30008, status.HTTP_400_BAD_REQUEST)
    activity.status = Activity.Status.CANCELLED
    activity.cancel_reason = reason.strip()
    activity.save(update_fields=["status", "cancel_reason", "updated_at"])
    from apps.signups.services import cancel_signups_for_activity

    cancel_signups_for_activity(activity, reason)
    return activity


def add_favorite(user, activity: Activity) -> bool:
    if activity.status not in {Activity.Status.PUBLISHED, Activity.Status.ENDED}:
        raise BusinessError("活动不可收藏", 30004, status.HTTP_404_NOT_FOUND)
    _, created = Favorite.objects.get_or_create(user=user, activity=activity)
    return created


def remove_favorite(user, activity: Activity):
    Favorite.objects.filter(user=user, activity=activity).delete()


def user_can_view_activity(user, activity: Activity) -> bool:
    if activity.is_deleted:
        return False
    if activity.status in {Activity.Status.PUBLISHED, Activity.Status.ENDED}:
        return True
    if not user or not user.is_authenticated:
        return False
    return (
        activity.organizer_id == user.id
        or can_admin_manage(user)
        or user_has_permission(user, "activity:audit")
    )


@transaction.atomic
def save_category(category_id: int | None, validated_data: dict):
    from .models import ActivityCategory

    try:
        if category_id:
            category = ActivityCategory.objects.filter(
                pk=category_id, is_deleted=False
            ).first()
            if not category:
                raise BusinessError("分类不存在", 30004, status.HTTP_404_NOT_FOUND)
            for field, value in validated_data.items():
                setattr(category, field, value)
            category.save()
            return category
        return ActivityCategory.objects.create(**validated_data)
    except IntegrityError:
        raise BusinessError(
            "分类标识 slug 已存在", 30009, status.HTTP_409_CONFLICT
        ) from None


@transaction.atomic
def save_tag(tag_id: int | None, validated_data: dict):
    from .models import ActivityTag

    try:
        if tag_id:
            tag = ActivityTag.objects.filter(pk=tag_id, is_deleted=False).first()
            if not tag:
                raise BusinessError("标签不存在", 30004, status.HTTP_404_NOT_FOUND)
            for field, value in validated_data.items():
                setattr(tag, field, value)
            tag.save()
            return tag
        return ActivityTag.objects.create(**validated_data)
    except IntegrityError:
        raise BusinessError(
            "标签名称已存在", 30009, status.HTTP_409_CONFLICT
        ) from None
