from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView

from .forms import PlayerProfileCreationForm
from .models import PlayerProfile


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
