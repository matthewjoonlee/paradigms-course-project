from django.urls import path

from .views import (
    HomeView,
    LoginView,
    PlayerProfileCreateView,
    PlayerProfileDetailView,
    PlayerProfileListView,
    buy_plays,
    logout_view,
    game_select,
    game_play,
    game_guess,
    dashboard,
)

app_name = "worndly"

urlpatterns = [
    #feature 1.1
    path("", HomeView.as_view(), name="home"),
    path("profiles/", PlayerProfileListView.as_view(), name="profile_list"),
    path("profiles/new/", PlayerProfileCreateView.as_view(), name="profile_create"),
    path("profiles/<int:pk>/", PlayerProfileDetailView.as_view(), name="profile_detail"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("buy-plays/", buy_plays, name="buy_plays"),

    # feature 2.1
    path("game/", game_select, name="game_select"),
    path("game/<int:pk>/", game_play, name="game_play"),
    path("game/<int:pk>/guess/", game_guess, name="game_guess"),

    # feature 3.1
    path("dashboard/", dashboard, name="dashboard"),
]
