from django.urls import path
from . import views

app_name = 'wellness'

urlpatterns = [
    path('alerts/', views.alerts_view, name='alerts'),
    path('alerts/<int:pk>/read/', views.mark_alert_read, name='mark_alert_read'),
    path('exercises/', views.exercises_view, name='exercises'),
    path('resources/', views.resources_view, name='resources'),
]
