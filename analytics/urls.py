from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('insights/', views.insights_view, name='insights'),
    path('trends/', views.trends_view, name='trends'),
    path('api/trends/', views.trend_data_api, name='trend_data'),
]
