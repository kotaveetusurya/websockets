from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    isonline = models.BooleanField(default=False)
    # Add any other fields that you need to extend the user with

    def __str__(self):
        return f'{self.user.username} Profile'

class Room(models.Model):
    name = models.CharField(max_length=200,unique=True)
    logo = models.ImageField(upload_to= 'roomLogos/', blank=True, null=True)
    slug = models.SlugField(max_length=50,unique=True)
    roomtype = models.CharField(default = 'group', max_length=10)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)  # Users who have read the message

    def __str__(self):
        return f'{self.user.username} - {self.message[:50]}'


class RoomMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    joined_on = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user.username} - {self.room.name}'
    
# to track unread messages of disconnected users===========================================
class UserRoomStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    unread_count = models.IntegerField(default=0)  # Tracks unread messages count for each user in the room

    def __str__(self):
        return f'{self.user.username} - {self.room.name} - {self.unread_count}'

class FriendRequest(models.Model):
    # Sender of the friend request
    sender = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    
    # Recipient of the friend request
    recipient = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    
    # Status of the request (pending, accepted, or rejected)
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    
    # Timestamps for when the request was created and last updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Friend request from {self.sender.username} to {self.recipient.username} - {self.status}"

    class Meta:
        unique_together = ('sender', 'recipient')
    
class Friendship(models.Model):
    user1 = models.ForeignKey(User, related_name='friendship_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='friendship_user2', on_delete=models.CASCADE)
    room = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"{self.user1.username} is friends with {self.user2.username}"

    @classmethod
    def are_friends(cls, user1, user2):
        """
        Check if two users are friends
        """
        return cls.objects.filter(
            (models.Q(user1=user1) & models.Q(user2=user2)) | 
            (models.Q(user1=user2) & models.Q(user2=user1))
        ).exists()
