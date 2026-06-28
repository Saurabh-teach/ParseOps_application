from django.urls import path
from .views import ChatRoomViewSet, MessageViewSet

room_list = ChatRoomViewSet.as_view({
    'get': 'list'
})
room_detail = ChatRoomViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})
create_direct = ChatRoomViewSet.as_view({
    'post': 'create_direct'
})
create_group = ChatRoomViewSet.as_view({
    'post': 'create_group'
})

message_list = MessageViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
message_detail = MessageViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    path('org/<str:org_slug>/chat/rooms/', room_list, name='room-list'),
    path('org/<str:org_slug>/chat/rooms/<uuid:pk>/', room_detail, name='room-detail'),
    path('org/<str:org_slug>/chat/rooms/direct/', create_direct, name='room-create-direct'),
    path('org/<str:org_slug>/chat/rooms/group/', create_group, name='room-create-group'),
    
    path('org/<str:org_slug>/chat/rooms/<uuid:room_pk>/messages/', message_list, name='message-list'),
    path('org/<str:org_slug>/chat/rooms/<uuid:room_pk>/messages/<uuid:pk>/', message_detail, name='message-detail'),
]
