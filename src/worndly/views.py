import os
import random
from datetime import timedelta
from urllib.parse import quote

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LoginForm, PlayerProfileCreationForm, PurchasePlaysForm
from .models import PlayerProfile, Game, Guess

# path to the folder containing the word list .txt files
WORDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "words")
FREE_GAMES_PER_DAY = 3

def load_words(language):
    # reads the word file for selected language
    filepath = os.path.join(WORDS_DIR, f"{language}.txt")
    with open(filepath, "r", encoding="utf-8") as f:
        words = {line.strip().lower() for line in f if len(line.strip()) == 5}

    return words

def pick_random_word(language):
    # picks and returns 5-letter word from selected language's word list
    word = load_words(language)
    return random.choice(list(word))

def evaluate_guess(guess_word, target_word):
    # compares guessed word against target word
    # G (green) = correct letter & position 
    # Y (yellow) = word includes letter, wrong position
    # X (grey) = letter not in word

    result = ["X", "X", "X", "X", "X"]
    target_list = list(target_word)
    guess_list = list(guess_word)

    # 1st pass: mark greens
    for i in range(5):
        if guess_list[i] == target_list[i]:
            result[i] = "G"
            # mark as used
            target_list[i] = None
            guess_list[i] = None

    # 2nd pass: mark yellows
    for i in range(5):
        if guess_list[i] is not None and guess_list[i] in target_list:
            result[i] = "Y"
            # remove letter to handle duplicates correctly
            target_list[target_list.index(guess_list[i])] = None

    return "".join(result)

def games_played_today(user):
    # returns number of games user has played today
    today = timezone.now().date()
    return Game.objects.filter(player=user, created_at__date=today).count()


def get_player_profile(user):
    # keep gameplay and purchases tied to one profile record
    profile, _ = PlayerProfile.objects.get_or_create(user=user, defaults={"name": ""})
    return profile


def kratos_headers():
    return {
        "Authorization": f"Bearer {settings.KRATOS_ACCESS_TOKEN}"
    }


def kratos_balance_url(email):
    encoded_email = quote(email, safe="")
    return f"{settings.KRATOS_API_BASE_URL}/{settings.KRATOS_GROUP_PATH}/player/{encoded_email}/"


def kratos_pay_url(email):
    encoded_email = quote(email, safe="")
    return f"{settings.KRATOS_API_BASE_URL}/{settings.KRATOS_GROUP_PATH}/player/{encoded_email}/pay"


def view_balance_for_user(email):
    # read the current coin balance from the external api
    api_response = requests.get(kratos_balance_url(email), headers=kratos_headers(), timeout=10)
    return api_response


def user_pay(email, amount):
    # charge the external api for the requested number of plays
    data = {"amount": amount}
    api_response = requests.post(
        kratos_pay_url(email),
        headers=kratos_headers(),
        data=data,
        timeout=10,
    )
    return api_response

class HomeView(TemplateView):
    template_name = "worndly/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_count"] = PlayerProfile.objects.count()
        context["recent_profiles"] = PlayerProfile.objects.select_related("user")[:5]
        return context


class PlayerProfileCreateView(FormView):
    template_name = "worndly/profile_form.html"
    form_class = PlayerProfileCreationForm

    def form_valid(self, form):
        # subfeature 1.1 creates both the auth account and its linked player profile
        try:
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
        except IntegrityError:
            form.add_error("username", "That username is already taken.")
            return self.form_invalid(form)

        profile = PlayerProfile.objects.create(
            user=user,
            name=form.cleaned_data["name"],
        )
        login(self.request, user)
        self.profile = profile
        return super().form_valid(form)

    def get_success_url(self):
        return self.profile.get_absolute_url()


class PlayerProfileListView(ListView):
    model = PlayerProfile
    template_name = "worndly/profile_list.html"
    context_object_name = "profiles"
    queryset = PlayerProfile.objects.select_related("user")


class PlayerProfileDetailView(DetailView):
    model = PlayerProfile
    template_name = "worndly/profile_detail.html"
    context_object_name = "profile"


class LoginView(FormView):
    template_name = "worndly/login.html"
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        # keep logged in users out of the login form
        if request.user.is_authenticated:
            return redirect("worndly:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = authenticate(
            self.request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is None:
            form.add_error(None, "Invalid username or password.")
            return self.form_invalid(form)
        login(self.request, user)
        return redirect("worndly:dashboard")


def logout_view(request):
    # feature 1 3 ends the current session
    logout(request)
    return redirect("worndly:home")


# 2.1: GAMEPLAY VIEWS

@login_required(login_url="worndly:login")
def game_select(request):
    # GET:  Show the language selection page.
    # POST: Validate  selected language, check daily game quota, create new Game, redirect to game board.
    
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German"),
        ("pt", "Portuguese"),
    ]
    error = None
    show_purchase_link = False

    if request.method == "POST":
        language = request.POST.get("language")
        valid_languages = [code for code, _ in LANGUAGE_CHOICES]

        # ensure submitted language is a valid option
        if language not in valid_languages:
            error = "Please select a valid language."
        else:
            # check if user has hit their daily free game limit
            played_today = games_played_today(request.user)
            profile = get_player_profile(request.user)
            if played_today >= FREE_GAMES_PER_DAY:
                if profile.extra_plays_remaining > 0:
                    word = pick_random_word(language)
                    game = Game.objects.create(
                        player=request.user,
                        language=language,
                        target_word=word,
                    )
                    profile.extra_plays_remaining -= 1
                    profile.save(update_fields=["extra_plays_remaining"])
                    return redirect("worndly:game_play", pk=game.pk)
                else:
                    error = f"You've used all {FREE_GAMES_PER_DAY} free games for today. Please purchase more plays to continue."
                    show_purchase_link = True
            else:
                # pick a random word and create a new game in the database
                word = pick_random_word(language)
                game = Game.objects.create(
                    player=request.user,
                    language=language,
                    target_word=word,
                )
                return redirect("worndly:game_play", pk=game.pk)

    return render(request, "worndly/game_select.html", {
        "languages": LANGUAGE_CHOICES,
        "error": error,
        "show_purchase_link": show_purchase_link,
    })


@login_required(login_url="worndly:login")
def game_play(request, pk):

    # renders game board for a specific game.
    # builds  guess history and keyboard letter states to pass to the template.

    # only allow the owner of the game to view it
    game = get_object_or_404(Game, pk=pk, player=request.user)
    guesses = game.guesses.all()

    # build a list of letter/result pairs for each completed guess row
    guess_data = []
    for g in guesses:
        letters = [{"letter": ch, "result": res} for ch, res in zip(g.word.upper(), g.result)]
        guess_data.append(letters)

    # track the best known state for each letter for the on-screen keyboard
    # priority: G > Y > X
    priority = {"G": 3, "Y": 2, "X": 1}
    letter_states = {}
    for g in guesses:
        for ch, res in zip(g.word.upper(), g.result):
            current = letter_states.get(ch)
            if current is None or priority[res] > priority[current]:
                letter_states[ch] = res

    return render(request, "worndly/game_play.html", {
        "game": game,
        "guesses": guess_data,
        "letter_states": letter_states,
        "max_attempts": 6,
        "attempts_left": 6 - game.attempts,
        "game_over": game.won is not None,
    })


@login_required(login_url="worndly:login")
def game_guess(request, pk):
    # AJAX endpoint that receives guessed word via POST, validates it, evaluates it, saves to database, and returns result as JSON.

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    # only allow  owner of the game to submit guesses
    game = get_object_or_404(Game, pk=pk, player=request.user)

    # reject guesses if the game is already finished
    if game.won is not None:
        return JsonResponse({"error": "Game is already over."}, status=400)

    guess_word = request.POST.get("guess", "").strip().lower()

    # validate: must be exactly 5 letters long 
    if len(guess_word) != 5 or not guess_word.isalpha():
        return JsonResponse({"error": "Please enter a valid 5-letter word."}, status=400)

    # validate: must exist in  word list for the selected language
    valid_words = load_words(game.language)
    if guess_word not in valid_words:
        return JsonResponse({"error": f'"{guess_word.upper()}" is not in the word list. Try again.'}, status=400)

    # evaluate guess and save it
    result = evaluate_guess(guess_word, game.target_word)
    Guess.objects.create(game=game, word=guess_word, result=result)
    game.attempts += 1

    # check if  player won or ran out of attempts
    if result == "GGGGG":
        game.won = True
    elif game.attempts >= 6:
        game.won = False
    game.save()

    return JsonResponse({
        "result": result,
        "guess": guess_word.upper(),
        "attempts": game.attempts,
        "game_over": game.won is not None,
        "won": game.won,
        # only reveal the target word when the game is over
        "target_word": game.target_word.upper() if game.won is not None else None,
    })


# feature 3.1

@login_required(login_url="worndly:login")
def dashboard(request):
    # shows a filterable history of all games played by the current user.
    active_filter = request.GET.get("filter", "all")
    now = timezone.now()
    profile = get_player_profile(request.user)

    games = Game.objects.filter(player=request.user)

    if active_filter == "week":
        games = games.filter(created_at__gte=now - timedelta(weeks=1))
    elif active_filter == "month":
        games = games.filter(created_at__gte=now - timedelta(days=30))
    elif active_filter == "year":
        games = games.filter(created_at__gte=now - timedelta(days=365))

    games = games.order_by("-created_at")

    return render(request, "worndly/dashboard.html", {
        "games": games,
        "active_filter": active_filter,
        "extra_plays_remaining": profile.extra_plays_remaining,
    })


@login_required(login_url="worndly:login")
def buy_plays(request):
    # feature 4 1 lets a user buy extra game plays
    profile = get_player_profile(request.user)
    form = PurchasePlaysForm(request.POST or None)
    balance = None
    error = None
    success = None

    if not settings.KRATOS_ACCESS_TOKEN:
        error = "kratos access token is missing"
        return render(request, "worndly/buy_plays.html", {
            "form": form,
            "balance": balance,
            "error": error,
            "success": success,
            "extra_plays_remaining": profile.extra_plays_remaining,
        })

    try:
        balance_response = view_balance_for_user(request.user.email)
        balance_data = balance_response.json()
        if balance_response.status_code == 200:
            balance = balance_data.get("amount")
        else:
            error = balance_data.get("detail") or balance_data.get("message") or "could not load current balance"
    except requests.RequestException:
        error = "could not reach the coin api"
    except ValueError:
        error = "received an invalid balance response"

    if request.method == "POST" and form.is_valid() and error is None:
        amount = form.cleaned_data["amount"]
        try:
            pay_response = user_pay(request.user.email, amount)
            pay_data = pay_response.json()
            if pay_response.status_code == 200:
                profile.extra_plays_remaining += amount
                profile.save(update_fields=["extra_plays_remaining"])
                success = f"purchase successful and {amount} extra plays were added"
                balance = pay_data.get("new_amount", balance)
                form = PurchasePlaysForm()
            else:
                error = pay_data.get("detail") or pay_data.get("message") or "purchase failed"
        except requests.RequestException:
            error = "could not reach the coin api"
        except ValueError:
            error = "received an invalid purchase response"

    return render(request, "worndly/buy_plays.html", {
        "form": form,
        "balance": balance,
        "error": error,
        "success": success,
        "extra_plays_remaining": profile.extra_plays_remaining,
    })
