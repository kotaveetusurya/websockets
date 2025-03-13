from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Q

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from .forms import *
from .models import *
from .serializers import *

# Home view to display all rooms
class home(APIView):
    def get(self,request):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.username == 'admin':
            rooms = Room.objects.all()
        else:
            rooms = Room.objects.filter(id__in=RoomMember.objects.filter(user=request.user).values('room_id'))

        rooms = rooms.annotate(unread_count=Count(
            'message',
            filter=~Q(message__read_by=request.user)
        ))

        # Serialize the room data
        room_serializer = RoomSerializer(rooms, many=True)

        return render(request, 'home.html', {
            'rooms': room_serializer.data,
            'loggedinuser': request.user,
        })


class userChatView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        friends = Friendship.objects.filter(
            models.Q(user1=request.user) | models.Q(user2=request.user)
        )

        friend_profiles_with_details = []
        for friendship in friends:
            if friendship.user1 == request.user:
                friend_profile = UserProfile.objects.get(user=friendship.user2)
                friendship_detail = friendship
            else:
                friend_profile = UserProfile.objects.get(user=friendship.user1)
                friendship_detail = friendship

            # Serialize the friend profile and friendship details
            friend_profiles_with_details.append({
                'friend_profile': UserProfileSerializer(friend_profile).data,
                'friendship_detail': FriendshipSerializer(friendship_detail).data
            })

        return render(request, 'userchat.html', {
            'loggedinuser': request.user,
            'friend_profiles_with_details': friend_profiles_with_details,
        })


# view to list all users, and add them to the friends list
class userListView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        all_users = User.objects.exclude(id=request.user.id)
        friends = Friendship.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        ).values_list('user1', 'user2')

        friend_ids = set()
        for user1, user2 in friends:
            if user1 != request.user.id:
                friend_ids.add(user1)
            if user2 != request.user.id:
                friend_ids.add(user2)

        non_friends = all_users.exclude(id__in=friend_ids)

        non_friend_profiles = [user.profile for user in non_friends]

        # Serialize non-friend profiles
        non_friend_profiles_serializer = UserProfileSerializer(non_friend_profiles, many=True)

        received_requests = FriendRequest.objects.filter(recipient=request.user, status=FriendRequest.PENDING)
        sent_requests = FriendRequest.objects.filter(sender=request.user, status=FriendRequest.PENDING)

        received_requests_serializer = FriendRequestSerializer(received_requests, many=True)
        sent_requests_serializer = FriendRequestSerializer(sent_requests, many=True)

        return render(request, 'userlist.html', {
            'loggedinuser': request.user,
            'non_friend_profiles': non_friend_profiles_serializer.data,
            'received_requests': received_requests_serializer.data,
            'sent_requests': sent_requests_serializer.data,
        })

    # def post(self, request):
    #     user1 = request.user
    #     user2_id = request.POST.get('user2')
    #     user2 = get_object_or_404(User, id=user2_id)

    #     if not Friendship.are_friends(user1, user2):
    #         room = Room.objects.create(
    #             name=f"{user1.username} & {user2.username} Chat Room",
    #             slug=f"private_{user1.username}_{user2.username}_room",
    #             roomtype='private'
    #         )

    #         friendship = Friendship.objects.create(user1=user1, user2=user2, room=room)

    #         friendship_data = FriendshipSerializer(friendship).data

    #         return JsonResponse({'status':'success','message': 'User added to Friends List', 'friend': friendship_data}, status=200)
    #     else:
    #         return JsonResponse({'status':'fail','message': 'User already a friend'}, status=404)

class SendFriendRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sender = request.user
        recipient_id = request.data.get('user2')

        # Ensure recipient exists and is not the sender
        try:
            recipient = User.objects.get(id=recipient_id)
            if sender == recipient:
                return Response({'error': 'You cannot send a friend request to yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Recipient does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if a request already exists
        if FriendRequest.objects.filter(
            (Q(sender=sender) & Q(recipient=recipient)) |
            (Q(sender=recipient) & Q(recipient=sender))
        ).exists():
            return Response({'error': 'A friend request already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the friend request
        friend_request = FriendRequest.objects.create(sender=sender, recipient=recipient)
        return Response({
            'status': 'success',  # Custom status field for the response body
            'id': friend_request.id,  # Optionally include other details like the ID
            'sender': friend_request.sender.username,
            'recipient': friend_request.recipient.username
        }, status=status.HTTP_201_CREATED)

class AcceptFriendRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_request_id = request.data.get('request_id')
        try:
            friend_request = FriendRequest.objects.get(id=friend_request_id, recipient=request.user, status=FriendRequest.PENDING)
            friend_request.status = FriendRequest.ACCEPTED
            friend_request.save()
            user1 = friend_request.sender
            user2 = friend_request.recipient
            if not Friendship.are_friends(user1, user2):
                room = Room.objects.create(
                    name=f"{user1.username} & {user2.username} Chat Room",
                    slug=f"private_{user1.username}_{user2.username}_room",
                    roomtype='private'
                )

                friendship = Friendship.objects.create(user1=user1, user2=user2, room=room)

                friendship_data = FriendshipSerializer(friendship).data

                return JsonResponse({'status':'success','message': 'User added to Friends List', 'friend': friendship_data}, status=200)
            else:
                return JsonResponse({'status':'fail','message': 'User already a friend'}, status=404)
        except FriendRequest.DoesNotExist:
            return Response({'error': 'Friend request not found or already processed.'}, status=status.HTTP_404_NOT_FOUND)
        

class RejectFriendRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_request_id = request.data.get('request_id')
        try:
            friend_request = FriendRequest.objects.get(id=friend_request_id, recipient=request.user, status=FriendRequest.PENDING)
            friend_request.status = FriendRequest.REJECTED
            friend_request.save()
            return Response({'status':'success','message': 'Friend request rejected.'}, status=status.HTTP_200_OK)
        except FriendRequest.DoesNotExist:
            return Response({'error': 'Friend request not found or already processed.'}, status=status.HTTP_404_NOT_FOUND)
        

# Room view to return room data and messages in JSON
class room(APIView):
    def get(self,request, slug):
        try:
            room = Room.objects.get(slug=slug)
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)

        messages = Message.objects.filter(room=room)

        for message in messages:
            if request.user not in message.read_by.all():
                message.read_by.add(request.user)

        room_data = RoomSerializer(room).data

        message_data = MessageSerializer(messages, many=True).data

        return JsonResponse({
            'room': room_data,
            'messages': message_data,
            'loggedinuser': request.user.username,
        })

class adminpanel(APIView):
    def get(self,request):
        create_room_form = RoomForm()
        remove_user_form = RemoveUserForm()
        delete_room_form = RoomForm()
        user_room_form = UserRoomForm()

        return render(request, 'adminpanel.html', {
            'create_room_form': create_room_form,
            'remove_user_form': remove_user_form,
            'delete_room_form': delete_room_form,
            'user_room_form': user_room_form,
            'rooms': Room.objects.all(),
            'loggedinuser': request.user,
            'messages': messages.get_messages(request),
        })

    def post(self, request):
        if request.method == 'POST':
            form_type = request.POST.get('formType')

            if form_type == 'create_room':
                create_room_form = RoomForm(request.POST, request.FILES)
                if create_room_form.is_valid():
                    room = create_room_form.save()
                    admin_user = User.objects.get(username='admin')
                    RoomMember.objects.create(user=admin_user, room=room)

                    # Serialize room data
                    room_serializer = RoomSerializer(room)

                    return JsonResponse({'success': True, 'message': 'Room created successfully!', 'room': room_serializer.data})
                else:
                    return JsonResponse({'success': False, 'message': 'Room creation failed', 'errors': create_room_form.errors})

            elif form_type == 'add_remove_users':
                user_room_form = UserRoomForm(request.POST, request.FILES)
                if user_room_form.is_valid():
                    room = user_room_form.cleaned_data['room_id']
                    users = user_room_form.cleaned_data['users']
                    operation = user_room_form.cleaned_data['operation']

                    if operation == 'add':
                        for user in users:
                            room_member, created = RoomMember.objects.get_or_create(user=user, room=room)
                            if not created:
                                return JsonResponse({'success': False, 'message': f'{user.username} is already a member of {room.name}.'})
                        return JsonResponse({'success': True, 'message': f'Users have been added to {room.name}.'})

                    elif operation == 'remove':
                        for user in users:
                            RoomMember.objects.filter(user=user, room=room).delete()
                        return JsonResponse({'success': True, 'message': f'Users have been removed from {room.name}.'})

                return JsonResponse({'success': False, 'message': 'Form data is not valid.'})

            elif form_type == 'remove_user':
                remove_user_form = RemoveUserForm(request.POST)
                if remove_user_form.is_valid():
                    username = remove_user_form.cleaned_data['username']
                    try:
                        user = User.objects.get(username=username)
                        user.delete()
                        return JsonResponse({'success': True, 'message': f'User {username} has been removed successfully.'})
                    except User.DoesNotExist:
                        return JsonResponse({'success': False, 'message': f'User {username} does not exist.'})

            elif form_type == 'delete_room':
                room_id = request.POST.get('room_id')
                room = get_object_or_404(Room, id=room_id)
                room.delete()
                return JsonResponse({'success': True, 'message': 'Room deleted successfully!'})





