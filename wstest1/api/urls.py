from django.urls import path

from wsapp.views import *

urlpatterns = [
    path('', home.as_view(), name='home'),
    path('room/<str:slug>/', room.as_view(), name='room'),
    path('adminpanel/',adminpanel.as_view(), name='adminpanel'),
    path('userchat/',userChatView.as_view(), name='userchat'),
    path('userlist/',userListView.as_view(), name='userlist'),
    path('send_friend_request/', SendFriendRequest.as_view(), name='send_friend_request'),
    path('accept_friend_request/', AcceptFriendRequest.as_view(), name='accept_friend_request'),
    path('reject_friend_request/', RejectFriendRequest.as_view(), name='reject_friend_request'),
]