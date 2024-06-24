import json
from datetime import datetime
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from chat.models import Room, Chats
from chat.serializers import ChatsSerializer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_id = self.scope['url_route']['kwargs']['room_id']

        if self.user_id != "0":
            try:
                room = Room.objects.get(user_id=self.room_id)
                room.is_user_active = True
                room.user_lastactive = datetime.now()
                room.save()
            except Room.DoesNotExist:
                Room.objects.create(user_id=self.user_id, is_user_active=True, user_lastactive=datetime.now())
                data = {
                    "user_id": self.user_id,
                    "is_user_active": True
                }
                async_to_sync(self.channel_layer.group_add)(
                    "0", "0"
                )
                async_to_sync(self.channel_layer.group_send)(
                    "0", {"type": "chat1.message", "message": data}
                )
                async_to_sync(self.channel_layer.group_discard)(
                      "0", "0"
                )   
        elif self.user_id == "0":
            try:
                room = Room.objects.get(user_id=self.room_id)
                room.is_admin_active = True
                room.admin_lastactive = datetime.now()
                room.save()
            except:
                pass
        self.accept()
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_id, self.channel_name
        )


        
    def disconnect(self, close_code):
        if self.user_id != "0":
            try:
                room = Room.objects.get(user_id=self.user_id)
                room.is_user_active = False
                room.save()
            except Room.DoesNotExist:
                pass
        else:
            try:
                room = Room.objects.get(user_id=self.room_id)
                room.is_admin_active = False
                room.save()
            except Room.DoesNotExist:
                pass
       
        async_to_sync(self.channel_layer.group_discard)(
            self.room_id, self.channel_name
        )


    
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        la = Chats.objects.filter(room=self.room_id).order_by('-id').first()
        if text_data_json['type'] == "message":
            if self.user_id == "0":
                try:
                    if la.role == "user":
                        la.seen=True
                        la.seen_time_stamp=datetime.now()
                        la.save()
                except:
                    pass
                chat = Chats.objects.create(room=self.room_id,message=text_data_json['message'],message_type=text_data_json['message_type'], role="admin")
                data = {
                    'message': chat.message,
                    'seen':chat.seen,
                    'seen_time':chat.seen_time_stamp,
                    'type':chat.message_type
                }
                room = Room.objects.get(user_id=self.room_id)
                room.is_unread_user=True
                room.is_unread_admin=False
                room.save()
                async_to_sync(self.channel_layer.group_send)(
                    self.room_id, {"type": "chat.message", "message": data}
                )
            else:
                try:
                    if la.role == "admin":
                        la.seen=True
                        la.seen_time_stamp=datetime.now()
                        la.save()
                except:
                    pass
                chat = Chats.objects.create(room=self.room_id,message=text_data_json['message'],message_type=text_data_json['message_type'], role="user")
                data = {
                    'message': chat.message,
                    'seen':chat.seen,
                    'seen_time':chat.seen_time_stamp,
                    'type':chat.message_type
                }
                room = Room.objects.get(user_id=self.room_id)
                room.is_unread_admin=True    
                room.is_unread_user=False
                room.save()
                async_to_sync(self.channel_layer.group_send)(
                    self.room_id, {"type": "chat.message", "message": data}
                )
        elif text_data_json['type'] == "statusupdate":
            if self.user_id != "0":
                room = Room.objects.get(user_id=self.room_id)
                room.is_unread_user=False
                room.save()
                chats = Chats.objects.filter(room=self.room_id, role="admin").update(seen=True, seen_time_stamp=datetime.now())
                
            else:
                room = Room.objects.get(user_id=self.room_id)
                room.is_unread_admin=False
                room.save()
                chats = Chats.objects.filter(room=self.room_id, role="user").update(seen=True, seen_time_stamp=datetime.now())
           
            

    def chat_message(self, event):
        message = event["message"]
        sender_channel_name = "0"
        async_to_sync(self.channel_layer.group_discard)(
        self.room_id, self.user_id
        )
        self.send(text_data=json.dumps(message))
        
        # chatss = Chats.objects.filter(room=self.room_id).order_by("-id").first()
        # data = ChatsSerializer(chatss, many=False)
        # self.send(text_data=json.dumps(data.data))
        async_to_sync(self.channel_layer.group_add)(
        self.room_id, self.user_id
        )
    
    def dis_message(self, event):
        self.send(text_data=json.dumps(event))
        
    def chat1_message(self, event):
        self.send(text_data=json.dumps(event))
       

        

    