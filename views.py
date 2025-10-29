from rest_framework import viewsets, status, generics, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Event, RSVP, Review, User
from .serializers import EventSerializer, RSVPSerializer, ReviewSerializer
from .permissions import IsOrganizerOrReadOnly, IsInvitedOrPublic, IsOwnerOrOrganizerOrReadOnly

class EventPaginationMixin:
    pass  # global pagination already set in settings

class EventViewSet(viewsets.ModelViewSet):
    """
    /events/  (list, create)
    /events/{id}/ (retrieve, update, destroy)
    /events/{id}/rsvp/ (POST)
    /events/{id}/reviews/ (GET, POST)
    """
    queryset = Event.objects.all().select_related('organizer')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsInvitedOrPublic & IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_public', 'location']
    search_fields = ['title', 'location', 'organizer__username']
    ordering_fields = ['start_time', 'created_at']

    def get_queryset(self):
        """
        For listing: show public events, plus private events where user is invited or is organizer.
        """
        user = self.request.user
        qs = Event.objects.all().select_related('organizer')
        if self.action == 'list':
            public_qs = qs.filter(is_public=True)
            if user.is_authenticated:
                invited_qs = qs.filter(is_public=False).filter(models.Q(invited_users=user) | models.Q(organizer=user))
                return (public_qs | invited_qs).distinct()
            return public_qs
        return qs

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def get_permissions(self):
        # For retrieve/list we need IsInvitedOrPublic; for write ops also IsOrganizerOrReadOnly
        if self.action in ['retrieve', 'list']:
            permission_classes = [IsAuthenticatedOrReadOnly, IsInvitedOrPublic]
        else:
            permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]
        return [perm() for perm in permission_classes]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='rsvp')
    def rsvp(self, request, pk=None):
        """
        POST /events/{event_id}/rsvp/  - create or update RSVP for current user
        payload: {"status": "Going"| "Maybe" | "Not Going"}
        """
        event = self.get_object()
        if not event.is_public and not (event.invited_users.filter(pk=request.user.pk).exists() or event.organizer == request.user):
            return Response({"detail":"Not invited to this private event."}, status=status.HTTP_403_FORBIDDEN)

        status_val = request.data.get('status')
        if status_val not in dict(RSVP.STATUS_CHOICES):
            return Response({"status":"Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        rsvp, created = RSVP.objects.get_or_create(event=event, user=request.user, defaults={'status': status_val})
        if not created:
            rsvp.status = status_val
            rsvp.save()
        serializer = RSVPSerializer(rsvp, context={'request': request})
        return Response(serializer.data, status=(status.HTTP_201_CREATED if created else status.HTTP_200_OK))

    @action(detail=True, methods=['get','post'], permission_classes=[IsAuthenticatedOrReadOnly], url_path='reviews')
    def reviews(self, request, pk=None):
        event = self.get_object()
        if request.method == 'GET':
            qs = event.reviews.all()
            page = self.paginate_queryset(qs)
            serializer = ReviewSerializer(page or qs, many=True)
            return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)
        else:
            # POST a new review
            data = request.data.copy()
            data['event'] = event.id
            serializer = ReviewSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save(user=request.user, event=event)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RSVPDetailView(generics.UpdateAPIView):
    """
    PATCH /events/{event_id}/rsvp/{user_id}/ : Update RSVP created by user_id (owner or organizer)
    """
    serializer_class = RSVPSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrOrganizerOrReadOnly]

    def get_object(self):
        event_id = self.kwargs['event_id']
        user_id = self.kwargs['user_id']
        return get_object_or_404(RSVP, event__id=event_id, user__id=user_id)
