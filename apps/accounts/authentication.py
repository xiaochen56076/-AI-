from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


def access_blacklist_key(jti: str) -> str:
    return f"jwt:blacklist:access:{jti}"


class BlacklistAwareJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        jti = validated_token.get("jti")
        if jti and cache.get(access_blacklist_key(jti)):
            raise AuthenticationFailed("登录状态已失效，请重新登录")
        user = super().get_user(validated_token)
        if not user.is_active:
            raise AuthenticationFailed("账号已被禁用")
        return user
