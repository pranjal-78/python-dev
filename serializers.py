from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import UserProfile, Event, RSVP, Review

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'full_name', 'bio', 'location', 'profile_picture']

class EventSerializer(serializers.ModelSerializer):
    organizer = serializers.CharField(source='organizer.username', read_only=True)
    invited_user_ids = serializers.PrimaryKeyRelatedField(source='invited_users', many=True, queryset=User.objects.all(), write_only=True, required=False)
    invited_users = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = ['id','title','description','organizer','location','start_time','end_time','is_public','invited_users','invited_user_ids','created_at','updated_at']
        read_only_fields = ['organizer','created_at','updated_at','invited_users']

    def get_invited_users(self, obj):
        return [u.username for u in obj.invited_users.all()]

    def validate(self, data):
        start = data.get('start_time', getattr(self.instance, 'start_time', None))
        end = data.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and start >= end:
            raise serializers.ValidationError("start_time must be before end_time.")
        return data

    def create(self, validated_data):
        invited = validated_data.pop('invited_users', [])
        event = Event.objects.create(**validated_data)
        if invited:
            event.invited_users.set(invited)
        return event

    def update(self, instance, validated_data):
        invited = validated_data.pop('invited_users', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if invited is not None:
            instance.invited_users.set(invited)
        return instance

class RSVPSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RSVP
        fields = ['id','event','user','status','created_at']
        read_only_fields = ['id','created_at','user']

    def validate(self, data):
        event = data.get('event') or getattr(self.instance, 'event', None)
        if event and event.end_time and event.end_time <= timezone.now():
            raise serializers.ValidationError("Cannot RSVP to an event that already ended.")
        return data

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id','event','user','rating','comment','created_at']
        read_only_fields = ['id','created_at','user']

    def validate(self, data):
        # allow review only if user attended (RSVP Going) OR event ended
        request = self.context.get('request')
        event = data.get('event') or getattr(self.instance, 'event', None)
        if event and request and request.user.is_authenticated:
            from .models import RSVP
            attended = RSVP.objects.filter(event=event, user=request.user, status=RSVP.STATUS_GOING).exists()
            if not attended and event.end_time > timezone.now():
                raise serializers.ValidationError("You can only review events you've attended or after the event has ended.")
        return data
