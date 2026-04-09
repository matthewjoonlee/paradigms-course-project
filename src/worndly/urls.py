from django.urls import path

from .views import (
    HomeView,
    PlayerProfileCreateView,
    PlayerProfileDetailView,
    PlayerProfileListView,
    game_select,
    game_play,
    game_guess
)

app_name = "worndly"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("profiles/", PlayerProfileListView.as_view(), name="profile_list"),
    path("profiles/new/", PlayerProfileCreateView.as_view(), name="profile_create"),
    path("profiles/<int:pk>/", PlayerProfileDetailView.as_view(), name="profile_detail"),

    # feature 2.1
    path("game/", game_select, name="game_select"),
    path("game/<int:pk>/", game_play, name="game_play"),
    path("game/<int:pk>/guess/", game_guess, name="game_guess"),
]
