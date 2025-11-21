from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KMLJobViewSet

router = DefaultRouter()
router.register(r'jobs', KMLJobViewSet, basename='kmljob')

urlpatterns = [
    path('', include(router.urls)),
]
