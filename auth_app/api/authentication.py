from rest_framework_simplejwt.authentication import JWTAuthentication
"""
    Custom JWT authentication that reads tokens from cookies.

    This class extends SimpleJWT’s `JWTAuthentication` to support authentication
    using an `access_token` stored in an HTTP-only cookie. It first checks the
    `Authorization` header, and if no token is found, it looks for the cookie.

    Useful for web apps where JWTs are stored securely in cookies instead of
    being sent manually in headers.

    Returns:
        (user, validated_token): If authentication succeeds.
        None: If no valid token is found.
"""
class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get('access_token')

            if raw_token is None:
                return None
            
            validated_token = self.get_validated_token(raw_token)

            return self.get_user(validated_token), validated_token