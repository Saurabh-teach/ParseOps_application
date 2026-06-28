from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings

User = get_user_model()

@database_sync_to_async
def get_user(validated_token):
    try:
        user = User.objects.get(id=validated_token["user_id"])
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token")
        
        if not token:
            # Maybe it's in the subprotocols
            subprotocols = scope.get('subprotocols', [])
            for protocol in subprotocols:
                if protocol.startswith('token-'):
                    token = [protocol.split('-')[1]]
                    break

        if token:
            try:
                UntypedToken(token[0])
                decoded_data = jwt_decode(token[0], settings.SECRET_KEY, algorithms=["HS256"])
                scope['user'] = await get_user(decoded_data)
            except (InvalidToken, TokenError, Exception) as e:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
            
        return await self.inner(scope, receive, send)
