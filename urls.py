from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, RSVPDetailView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='events')

urlpatterns = [
    path('', include(router.urls)),
    # RSVP per-user update:
    path('events/<int:event_id>/rsvp/<int:user_id>/', RSVPDetailView.as_view(), name='rsvp-update'),
    # JWT token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
