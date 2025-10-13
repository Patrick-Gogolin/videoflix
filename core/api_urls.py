from django.urls import path, include

urlpatterns = [
    path('', include('auth_app.api.urls')),
    path('', include('video_app.api.urls'))
]