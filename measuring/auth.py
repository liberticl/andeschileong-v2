import jwt
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from .models import Device


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            token_prefix, token_key = auth_header.split()
            if token_prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None

        try:
            payload = jwt.decode(
                token_key, settings.CP_JWT_SECRET, algorithms=["HS256"])
            devname = payload.get('devicename')
            device = Device.objects.get(name=devname)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('El token ha expirado')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token inválido')
        except Device.DoesNotExist:
            raise AuthenticationFailed('Dispositivo no encontrado')

        return (device, payload)
