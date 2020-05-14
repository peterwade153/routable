from django.urls import path

from api import views


urlpatterns = [
    path('items', views.ItemCreateView.as_view(), name='create_item'),
    path('items/transaction', views.TransactionCreateView.as_view(), name='create_transaction'),
    path('items/move/<uuid:pk>/', views.MoveItemView.as_view(), name="move_item"),
    path('items/error/<uuid:pk>/', views.ErrorItemView.as_view(), name='error_item'),
    path('items/fix/<uuid:pk>/', views.FixItemView.as_view(), name='fix_item'),
]
