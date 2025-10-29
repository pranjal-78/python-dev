from rest_framework import permissions

class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Only organizer can modify or delete an event.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user

class IsInvitedOrPublic(permissions.BasePermission):
    """
    Allow access to an event if it is public OR user is the organizer OR user is invited.
    """

    def has_object_permission(self, request, view, obj):
        # Everyone can read public events
        if request.method in permissions.SAFE_METHODS:
            if obj.is_public:
                return True
            if request.user.is_authenticated:
                if obj.organizer == request.user:
                    return True
                if obj.invited_users.filter(pk=request.user.pk).exists():
                    return True
            return False
        # For write actions, rely on other permissions (e.g., IsOrganizerOrReadOnly)
        return True

class IsOwnerOrOrganizerOrReadOnly(permissions.BasePermission):
    """
    For RSVP patch: owner of the RSVP or the event organizer can update; read otherwise.
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # obj may be an RSVP or Review: allow if user is the owner or event organizer
        owner = getattr(obj, 'user', None)
        event = getattr(obj, 'event', None)
        if owner == request.user:
            return True
        if event and event.organizer == request.user:
            return True
        return False
