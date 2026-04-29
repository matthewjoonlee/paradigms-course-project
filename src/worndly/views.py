import os
import random
from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone


from .forms import PlayerProfileCreationForm
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


# 2.1: GAMEPLAY VIEWS

@login_required
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

    if request.method == "POST":
        language = request.POST.get("language")
        valid_languages = [code for code, _ in LANGUAGE_CHOICES]

        # ensure submitted language is a valid option
        if language not in valid_languages:
            error = "Please select a valid language."
        else:
            # check if user has hit their daily free game limit
            played_today = games_played_today(request.user)
            if played_today >= FREE_GAMES_PER_DAY:
                error = f"You've used all {FREE_GAMES_PER_DAY} free games for today. Please purchase more plays to continue."
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
    })


@login_required
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


@login_required
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


# feature 3.1 & 3.2

@login_required
def dashboard(request):
    # shows a filterable history of all games played by the current user,
    # plus overall statistics across all plays.
    active_filter = request.GET.get("filter", "all")
    now = timezone.now()

    games = Game.objects.filter(player=request.user)

    if active_filter == "week":
        games = games.filter(created_at__gte=now - timedelta(weeks=1))
    elif active_filter == "month":
        games = games.filter(created_at__gte=now - timedelta(days=30))
    elif active_filter == "year":
        games = games.filter(created_at__gte=now - timedelta(days=365))

    games = games.order_by("-created_at")

    # feature 3.2: compute statistics over all completed games (not filtered)
    all_completed = Game.objects.filter(player=request.user, won__isnull=False)
    total_completed = all_completed.count()
    games_won = all_completed.filter(won=True).count()
    win_rate = round(games_won / total_completed * 100) if total_completed else 0

    attempts_dist = [all_completed.filter(attempts=n).count() for n in range(1, 7)]

    return render(request, "worndly/dashboard.html", {
        "games": games,
        "active_filter": active_filter,
        "total_completed": total_completed,
        "games_won": games_won,
        "win_rate": win_rate,
        "attempts_dist": attempts_dist,
    })
