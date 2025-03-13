import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Room, RoomMember, UserRoomStatus
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async

# Global dictionary to track connected users per room
CONNECTED_USERS = {}

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f"chat_{self.room_slug}"
        self.user = self.scope["user"]

        # Ensure the room has a set of connected users, or create it
        if self.room_slug not in CONNECTED_USERS:
            CONNECTED_USERS[self.room_slug] = set()

        # Add the user to the room's connected users set
        CONNECTED_USERS[self.room_slug].add(self.user.username)

        # Add the user to the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Reset unread count for the connected user
        await self.reset_unread_count(self.user, self.room_slug)

        # Ensure unread count is awaited before sending
        unread_count_dict = await self.get_unread_count_for_all_disconnected_users(self.room_slug)

        print('unread messages dict', unread_count_dict)

        # Send the unread count as a JSON response
        await self.send(text_data=json.dumps({
            'type': 'connection_success',
            'slug': self.room_slug,
            'unread_count_dict': unread_count_dict,  # Awaited result of the function
            'unread_count': 0,
            'online_users_count': len(CONNECTED_USERS[self.room_slug])
        }))

    async def disconnect(self, close_code):
        # Remove the user from the room's connected users set
        CONNECTED_USERS[self.room_slug].remove(self.user.username)

        # If there are no more users in the room, remove the entry for the room
        if len(CONNECTED_USERS[self.room_slug]) == 0:
            del CONNECTED_USERS[self.room_slug]

        # Remove the user from the room group when they disconnect
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = text_data_json['user']
        room_slug = text_data_json['slug']

        # Save the message in the database
        message_obj = await self.save_message(user, message, room_slug)

        # Now, we check all group members and increment unread count for disconnected users
        await self.increment_unread_count_for_disconnected_users(room_slug)

        # Send the message to the room group along with the unread count for disconnected users
        unread_count_dict = await self.get_unread_count_for_all_disconnected_users(room_slug)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user,
                'unread_count': unread_count_dict  # Awaited result here too
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        unread_count = event['unread_count']

        # Send message and unread count to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message,
            'user': user,
            'unread_count': unread_count
        }))

    @database_sync_to_async
    def get_unread_count_for_all_disconnected_users(self, room_slug):
        # Get all room members
        room = Room.objects.get(slug=room_slug)
        room_members = RoomMember.objects.filter(room=room)

        unread_count_dict = {}
        for room_member in room_members:
            user = room_member.user
            if user.username not in CONNECTED_USERS.get(room_slug, set()):  # If user is disconnected
                unread_count = Message.objects.filter(room=room).exclude(read_by=user).count()
                print('unread-user', user.email)
                print('unread count-', unread_count)
                unread_count_dict[user.username] = unread_count
        return unread_count_dict

    @database_sync_to_async
    def save_message(self, user, message_text, room_slug):
        # Save the received message in the database
        room = Room.objects.get(slug=room_slug)
        user = User.objects.get(username=user)
        message = Message.objects.create(
            room=room,
            user=user,
            message=message_text,
        )
        message.read_by.add(user)
        return message

    @database_sync_to_async
    def increment_unread_count_for_disconnected_users(self, room_slug):
        # Increment unread count for disconnected users
        room = Room.objects.get(slug=room_slug)
        room_members = RoomMember.objects.filter(room=room)

        for room_member in room_members:
            user = room_member.user
            if user.username not in CONNECTED_USERS.get(room_slug, set()):  # If user is disconnected
                print('disconnected user-',user.username)
                user_room_status, created = UserRoomStatus.objects.get_or_create(
                    user=user,
                    room=room
                )
                # Increment unread count for the user
                user_room_status.unread_count += 1
                user_room_status.save()

    @database_sync_to_async
    def reset_unread_count(self, user, room_slug):
        # Get the room
        room = Room.objects.get(slug=room_slug)

        # Get or create the user-room status record
        user_room_status, created = UserRoomStatus.objects.get_or_create(
            user=user,
            room=room
        )

        # Reset the unread count to 0
        user_room_status.unread_count = 0
        user_room_status.save()


class GlobalUnreadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_group_name = "global_unread_group"  # This group will represent all globally connected users

        # Add the user to the global connected users group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Get unread counts for all users
        unread_counts = await self.get_all_unread_counts()

        # Send unread counts to all globally connected users (broadcast)
        await self.broadcast_unread_counts(unread_counts)

    async def broadcast_unread_counts(self, unread_counts):
        # Send the unread counts to all globally connected users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_unread_counts_to_all',
                'unread_counts': unread_counts
            }
        )

    async def send_unread_counts_to_all(self, event):
        unread_counts = event['unread_counts']

        # Send the unread counts to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'unread_counts',
            'unread_counts': unread_counts
        }))

    async def disconnect(self, close_code):
        # This will handle the disconnection logic if needed
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def get_all_unread_counts(self):
        unread_counts = {}

        # Get all RoomMembers and associated rooms
        room_members = RoomMember.objects.all()

        # Iterate over all room members to get unread count per user per room
        for room_member in room_members:
            user = room_member.user
            room = room_member.room

            # Count unread messages for this user in the current room
            unread_count = Message.objects.filter(room=room).exclude(read_by=user).count()

            # If the user is not in the dictionary, initialize it
            if room.slug not in unread_counts:
                unread_counts[room.slug] = {}

            # Add the unread count for the user in the room
            unread_counts[room.slug][user.username] = unread_count

        return unread_counts


class PrivateChatConsumer(AsyncWebsocketConsumer):
    online_users = {}
    async def connect(self):
        self.user1 = self.scope['url_route']['kwargs']['user1']
        self.user2 = self.scope['url_route']['kwargs']['user2']
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']  # Get the room slug from the URL
        print('room slug', self.room_slug)

        # Get the room object based on the room slug
        try:
            room = await self.get_room_by_slug(self.room_slug)
            print('room', room.roomtype)
        except Room.DoesNotExist:
            await self.close()
            return

        self.room_group_name = f"private_chat_{self.room_slug}"

        self.user = self.scope["user"]

        # Mark user as online in the dictionary
        PrivateChatConsumer.online_users[self.user.username] = True
        print(PrivateChatConsumer.online_users)

        await self.accept()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # Broadcast online status to both users (this can be extended to more users if needed)
        await self.send_user_status()

        # Send a success message to the frontend
        await self.send(text_data=json.dumps({
            'type': 'private_connection_successful',
            'message': f'You are connected to user {self.user2}',
            'user1': self.user1,
            'user2': self.user2,
            'room_slug': self.room_slug,  # Send the room slug as part of the message
        }))

    async def disconnect(self, close_code):
        # Mark user as offline in the dictionary
        PrivateChatConsumer.online_users[self.user.username] = False
        
        # Broadcast offline status to both users (this can be extended to more users if needed)
        await self.send_user_status()

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = text_data_json['user']

        # Fetch the room object using the room slug
        room = await self.get_room_by_slug(self.room_slug)

        # Save the private message in the database, associating it with the room
        await self.save_private_message(user, message, room)

        # Send the message to the private chat group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'private_chat_message',
                'message': message,
                'user': user
            }
        )

    async def private_chat_message(self, event):
        message = event['message']
        user = event['user']

        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message,
            'user': user
        }))

    @database_sync_to_async
    def save_private_message(self, user, message_text, room):
        sender = User.objects.get(username=user)
        receiver = User.objects.get(username=self.user1 if sender.username != self.user1 else self.user2)

        # Save the private chat message in the database, linking it to the correct room
        message = Message.objects.create(
            room=room,  # Associate the message with the room
            user=sender,
            message=message_text,
        )
        # Add both sender and receiver to the read_by field
        message.read_by.add(sender, receiver)
        return message

    @database_sync_to_async
    def get_room_by_slug(self, room_slug):
        # Fetch the room using the room slug
        return Room.objects.get(slug=room_slug)
    
    async def send_user_status(self):
        print('Inside send_user_status method')
        
        # Confirm that the correct group name and users are being sent
        print(f'Group name: {self.room_group_name}, user1: {self.user1}, user2: {self.user2}')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user1': self.user1,
                'user2': self.user2,
                'room_slug': self.room_slug,
                'user1_status': 'online' if PrivateChatConsumer.online_users.get(self.user1, False) else 'offline',
                'user2_status': 'online' if PrivateChatConsumer.online_users.get(self.user2, False) else 'offline'
            }
        )


    async def user_status(self, event):
        print('self send called')
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user1': event['user1'],
            'user2': event['user2'],
            'room_slug': event['room_slug'],
            'user1_status': event['user1_status'],
            'user2_status': event['user2_status']
        }))


