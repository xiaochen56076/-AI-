from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone
from rest_framework import status

from apps.accounts.models import User
from apps.activities.models import Activity
from apps.activities.services import can_admin_manage, can_manage_activity
from common.exceptions import BusinessError

from .models import Signup

ACTIVE_SIGNUP_STATUSES = {
    Signup.Status.WAITLIST,
    Signup.Status.SUCCESS,
    Signup.Status.CHECKED_IN,
}


def _signup_error(message: str, code: int, http_status: int, signup: Signup | None = None):
    data = None
    if signup:
        data = {
            "signup_id": signup.pk,
            "status": signup.status,
            "status_text": signup.status_text,
        }
    raise BusinessError(message, code, http_status, data)


def _next_queue_no(activity: Activity) -> int:
    current = Signup.objects.filter(activity=activity).aggregate(value=Max("queue_no"))["value"]
    return (current or 0) + 1


def _apply_existing_signup(signup: Signup, **values):
    for field, value in values.items():
        setattr(signup, field, value)
    signup.save()
    return signup


@transaction.atomic
def signup_for_activity(activity_id: int, user: User, remark: str = "") -> tuple[Signup, bool]:
    activity = (
        Activity.objects.select_for_update()
        .select_related("category")
        .filter(pk=activity_id, is_deleted=False)
        .first()
    )
    if not activity:
        raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
    if activity.status != Activity.Status.PUBLISHED:
        _signup_error("活动当前不可报名", 40004, status.HTTP_409_CONFLICT)
    now = timezone.now()
    if now < activity.signup_start:
        _signup_error("报名尚未开始", 40005, status.HTTP_409_CONFLICT)
    if now > activity.signup_end:
        _signup_error("报名已截止", 40006, status.HTTP_409_CONFLICT)
    if not user.is_active:
        _signup_error("账号已被禁用", 20004, status.HTTP_403_FORBIDDEN)

    existing = Signup.objects.select_for_update().filter(activity=activity, user=user).first()
    if existing and existing.status in ACTIVE_SIGNUP_STATUSES:
        _signup_error("你已报名该活动，请勿重复提交", 40002, status.HTTP_409_CONFLICT, existing)
    if existing and existing.status == Signup.Status.NO_SHOW:
        _signup_error("该活动已结束，无法重新报名", 40004, status.HTTP_409_CONFLICT, existing)

    if activity.signup_count < activity.capacity:
        claimed = Activity.objects.filter(
            pk=activity.pk,
            status=Activity.Status.PUBLISHED,
            signup_count__lt=F("capacity"),
        ).update(signup_count=F("signup_count") + 1)
        if claimed:
            activity.signup_count += 1
            if existing:
                signup = _apply_existing_signup(
                    existing,
                    status=Signup.Status.SUCCESS,
                    queue_no=None,
                    remark=remark[:255],
                    cancel_at=None,
                    signup_at=now,
                )
            else:
                signup = Signup.objects.create(
                    activity=activity,
                    user=user,
                    status=Signup.Status.SUCCESS,
                    remark=remark[:255],
                )
            return signup, True

    waitlist_available = activity.waitlist_enabled and (
        activity.waitlist_limit == 0 or activity.waitlist_count < activity.waitlist_limit
    )
    if waitlist_available:
        reserve = Activity.objects.filter(pk=activity.pk, waitlist_enabled=True)
        if activity.waitlist_limit:
            reserve = reserve.filter(waitlist_count__lt=F("waitlist_limit"))
        claimed = reserve.update(waitlist_count=F("waitlist_count") + 1)
        if claimed:
            activity.waitlist_count += 1
            queue_no = _next_queue_no(activity)
            if existing:
                signup = _apply_existing_signup(
                    existing,
                    status=Signup.Status.WAITLIST,
                    queue_no=queue_no,
                    remark=remark[:255],
                    cancel_at=None,
                    signup_at=now,
                )
            else:
                signup = Signup.objects.create(
                    activity=activity,
                    user=user,
                    status=Signup.Status.WAITLIST,
                    queue_no=queue_no,
                    remark=remark[:255],
                )
            return signup, True

    _signup_error("名额已满，候补队列也已满", 40001, status.HTTP_409_CONFLICT)


@transaction.atomic
def cancel_signup(activity_id: int, user: User) -> tuple[Signup, Signup | None]:
    activity = Activity.objects.select_for_update().filter(pk=activity_id, is_deleted=False).first()
    if not activity:
        raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
    signup = Signup.objects.select_for_update().filter(activity=activity, user=user).first()
    if not signup or signup.status not in {Signup.Status.SUCCESS, Signup.Status.WAITLIST}:
        raise BusinessError("没有可取消的有效报名", 40007, status.HTTP_409_CONFLICT)
    now = timezone.now()
    if now > activity.signup_end:
        raise BusinessError("报名已截止，无法取消", 40006, status.HTTP_409_CONFLICT)
    if activity.status in {Activity.Status.CANCELLED, Activity.Status.ENDED}:
        raise BusinessError("活动已取消或结束", 40004, status.HTTP_409_CONFLICT)

    promoted = None
    if signup.status == Signup.Status.SUCCESS:
        signup.status = Signup.Status.CANCELLED
        signup.cancel_at = now
        signup.save(update_fields=["status", "cancel_at", "updated_at"])
        Activity.objects.filter(pk=activity.pk, signup_count__gt=0).update(
            signup_count=F("signup_count") - 1
        )
        promoted = (
            Signup.objects.select_for_update()
            .filter(activity=activity, status=Signup.Status.WAITLIST)
            .order_by("queue_no", "id")
            .first()
        )
        if promoted:
            promoted.status = Signup.Status.SUCCESS
            promoted.save(update_fields=["status", "updated_at"])
            Activity.objects.filter(pk=activity.pk).update(
                waitlist_count=F("waitlist_count") - 1,
                signup_count=F("signup_count") + 1,
            )
    else:
        signup.status = Signup.Status.CANCELLED
        signup.cancel_at = now
        signup.save(update_fields=["status", "cancel_at", "updated_at"])
        Activity.objects.filter(pk=activity.pk, waitlist_count__gt=0).update(
            waitlist_count=F("waitlist_count") - 1
        )

    return signup, promoted


def cancel_signups_for_activity(activity: Activity, reason: str = ""):
    now = timezone.now()
    active = Signup.objects.filter(
        activity=activity,
        status__in=[Signup.Status.WAITLIST, Signup.Status.SUCCESS],
    )
    active.filter(status=Signup.Status.WAITLIST).update(
        status=Signup.Status.CANCELLED,
        cancel_at=now,
        remark=reason[:255],
        updated_at=now,
    )
    active.filter(status=Signup.Status.SUCCESS).update(
        status=Signup.Status.CANCELLED,
        cancel_at=now,
        remark=reason[:255],
        updated_at=now,
    )
    Activity.objects.filter(pk=activity.pk).update(signup_count=0, waitlist_count=0)


def ensure_can_manage_roster(user, activity: Activity):
    if not (can_manage_activity(user, activity) or can_admin_manage(user)):
        raise BusinessError("只能查看自己发布活动的报名名单", 30002, status.HTTP_403_FORBIDDEN)


def build_csv_rows(activity: Activity):
    signups = (
        Signup.objects.filter(activity=activity)
        .select_related("user")
        .order_by("status", "queue_no", "signup_at")
    )
    rows = []
    for signup in signups:
        rows.append(
            [
                signup.user.student_no,
                signup.user.real_name,
                signup.user.college,
                signup.get_status_display(),
                signup.queue_no or "",
                timezone.localtime(signup.signup_at).strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )
    return rows
