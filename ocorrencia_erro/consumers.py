import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage, Record, Notificacao
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.record_id = self.scope['url_route']['kwargs']['record_id']
        self.record_group_name = f'chat_{self.record_id}'

        await self.channel_layer.group_add(
            self.record_group_name,
            self.channel_name
        )
        await self.accept()

        chat_history = await self.get_chat_history()
        for message in chat_history:
            await self.send(text_data=json.dumps({
                'message': message['message'],
                'author': message['author__username'],
                'timestamp': message['timestamp'].isoformat()
            }))
            
    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.record_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        saved_message = await self.save_message(message)

        # Envia a mensagem para o grupo do chat
        await self.channel_layer.group_send(
            self.record_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'author': self.user.username,
                'timestamp': saved_message.timestamp.isoformat()
            }
        )

        # Lógica para enviar a notificação
        recipient_id = await self.get_recipient_id()
        if recipient_id:
            recipient_group_name = f'user_{recipient_id}'
            await self.channel_layer.group_send(
                recipient_group_name,
                {
                    'type': 'new_chat_message',  # <--- Este é o manipulador de evento no NotificationConsumer
                    'message': "Nova mensagem de chat",
                    'sender': self.user.username,
                    'record_id': self.record_id,
                }
            )
            print(f"RECEIVE: Notificação enviada para o grupo do usuário: {recipient_group_name}")
            await self.criar_notificacao_feedback(self.record_id, recipient_id, self.user.username)


    # No seu ChatConsumer.py

    @database_sync_to_async
    def criar_notificacao_feedback(self, record_id, recipient_user_id, sender_username):
        """
        Cria uma notificação quando uma nova mensagem de chat é enviada
        """
        try:
            record = Record.objects.get(id=record_id)
            usuario = User.objects.get(id=recipient_user_id)
            
            titulo = f"Nova mensagem na ocorrência #{record.codigo_externo or record.id}"
            resumo = f"{sender_username} mandou uma nova mensagem"
            
            Notificacao.objects.create(
                user=usuario,
                record=record,
                tipo='conversa_chat',  # Ou um tipo apropriado para o chat
                titulo=titulo,
                resumo=resumo
            )
            print("Notificação de mensagem criada com sucesso no banco de dados.")

        except Exception as e:
            print(f"Erro ao criar notificação de mensagem: {e}")


    async def chat_message(self, event):
        message = event['message']
        author = event['author']
        timestamp = event['timestamp']
        await self.send(text_data=json.dumps({
            'message': message,
            'author': author,
            'timestamp': timestamp
        }))
        
    @database_sync_to_async
    def get_chat_history(self):
        return list(
            ChatMessage.objects.filter(record_id=self.record_id)
            .select_related('author')
            .order_by('timestamp')
            .values('message', 'author__username', 'timestamp')
        )

    @database_sync_to_async
    def save_message(self, message):
        return ChatMessage.objects.create(
            record_id=self.record_id,
            author=self.user,
            message=message
        )

    @database_sync_to_async
    def get_recipient_id(self):
        try:
            ocorrencia = Record.objects.get(id=self.record_id)
            
            responsible_user = User.objects.filter(username=ocorrencia.responsible).first()
            if self.user.username == ocorrencia.responsible:
                # Substitua 'nome_de_usuario_do_gestor' pelo valor que você define manualmente
                manager_user = User.objects.filter(username='welton').first()
                return manager_user.id if manager_user else None
            else:
                return responsible_user.id if responsible_user else None
                
        except Record.DoesNotExist:
            return None