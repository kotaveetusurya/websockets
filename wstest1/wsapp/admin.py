from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Room)

admin.site.register(Message)

admin.site.register(RoomMember)

admin.site.register(UserProfile)

admin.site.register(UserRoomStatus)

admin.site.register(Friendship)

admin.site.register(FriendRequest)