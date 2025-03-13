from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = UserProfile
        fields = ['user', 'profile_picture', 'bio', 'isonline']


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name', 'logo', 'slug', 'roomtype', 'created_on']


class MessageSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Displaying the username of the related User model
    room = serializers.StringRelatedField()  # Displaying the room name
    
    # Using `read_by` field to represent a list of usernames who have read the message
    read_by = serializers.StringRelatedField(many=True)  

    class Meta:
        model = Message
        fields = ['id', 'room', 'user', 'message', 'created_on', 'read_by']


class RoomMemberSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Displaying the username of the related User model
    room = serializers.StringRelatedField()  # Displaying the room name
    
    class Meta:
        model = RoomMember
        fields = ['user', 'room', 'joined_on']


class UserRoomStatusSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Displaying the username of the related User model
    room = serializers.StringRelatedField()  # Displaying the room name

    class Meta:
        model = UserRoomStatus
        fields = ['user', 'room', 'unread_count']

class FriendRequestSerializer(serializers.ModelSerializer):
    # Use the related UserProfile for sender and recipient
    sender_profile_picture = serializers.ImageField(source='sender.profile.profile_picture', required=False)
    recipient_profile_picture = serializers.ImageField(source='recipient.profile.profile_picture', required=False)
    sender_bio = serializers.CharField(source='sender.profile.bio', required=False)
    recipient_bio = serializers.CharField(source='recipient.profile.bio', required=False)
    sender_isonline = serializers.BooleanField(source='sender.profile.isonline', required=False)
    recipient_isonline = serializers.BooleanField(source='recipient.profile.isonline', required=False)

    # Sender and recipient username and email
    sender_username = serializers.CharField(source='sender.username')
    recipient_username = serializers.CharField(source='recipient.username')
    sender_email = serializers.EmailField(source='sender.email')
    recipient_email = serializers.EmailField(source='recipient.email')
    
    # Friend request status
    status = serializers.ChoiceField(choices=FriendRequest.STATUS_CHOICES)

    class Meta:
        model = FriendRequest
        fields = [
            'sender', 'sender_username', 'sender_email', 'sender_profile_picture', 'sender_bio', 'sender_isonline',
            'recipient', 'recipient_username', 'recipient_email', 'recipient_profile_picture', 'recipient_bio', 'recipient_isonline',
            'status', 'created_at', 'updated_at','id'
        ]



class FriendshipSerializer(serializers.ModelSerializer):
    user1 = serializers.StringRelatedField()  # Displaying the username of the first user
    user2 = serializers.StringRelatedField()  # Displaying the username of the second user
    room = RoomSerializer()  # Serializing the Room object (in case it's not null)
    
    class Meta:
        model = Friendship
        fields = ['user1', 'user2', 'room', 'created_at']
