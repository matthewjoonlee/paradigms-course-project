from django.urls import path

from .views import (
    HomeView,
    PlayerProfileCreateView,
    PlayerProfileDetailView,
    PlayerProfileListView,
)

app_name = "worndly"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("profiles/", PlayerProfileListView.as_view(), name="profile_list"),
    path("profiles/new/", PlayerProfileCreateView.as_view(), name="profile_create"),
    path("profiles/<int:pk>/", PlayerProfileDetailView.as_view(), name="profile_detail"),
]
