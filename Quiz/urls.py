from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('participant/', views.participant_view, name='participant'),
    path('manage-quiz/add/', views.quiz_editor_view, name='add_quiz'),
    path('manage-quiz/<int:quiz_id>/edit/', views.quiz_editor_view, name='edit_quiz'),
    path('manage-quiz/<int:quiz_id>/delete/', views.delete_quiz_view, name='delete_quiz'),
    path('quiz/<int:quiz_id>/', views.take_quiz_view, name='take_quiz'),
]