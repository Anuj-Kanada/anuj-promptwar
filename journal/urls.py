from django.urls import path
from . import views

app_name = 'journal'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('new/', views.new_entry, name='new_entry'),
    path('entry/<int:pk>/', views.entry_detail, name='entry_detail'),
    path('history/', views.history, name='history'),
    path('mood/log/', views.quick_mood_log, name='quick_mood_log'),
]
