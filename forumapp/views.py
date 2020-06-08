import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.utils import timezone
from django.urls import reverse
from .models import UserSettings, Channel, Thread, Comment
from .forms import UserSettingsForm, ChannelForm, ThreadForm, CommentForm


def get_settings(user):
    us = UserSettings.objects.filter(user=user)
    if us.exists():
        return us.get()
    else:
        return UserSettings.objects.create(user=user)

class ViewMixin(generic.base.ContextMixin):
    initial = {'key': 'value'}

    def get_context_data(self, **kwargs):
        context = super(ViewMixin, self).get_context_data(**kwargs)

        if hasattr(self, 'form_class'):
            context['form'] = self.form_class(initial=self.initial)
        if hasattr(self, 'context_object_name'):
            context[self.context_object_name] = self.get_object()
        return context

# Show the settings menu TODO: 404 when not logged in
class UserSettingsView(ViewMixin, generic.DetailView):
    model = UserSettings
    template_name = 'forumapp/user_settings.html'

    form_class = UserSettingsForm

    queryset = UserSettings.objects

    def get_object(self):
        if self.request.user.is_authenticated:
            settings = self.queryset.filter(user=self.request.user)
            if settings.exists():
                return settings.get()
            else:
                return self.queryset.create(user=self.request.user)
        return self.queryset.none()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        return super(UserSettingsView, self).get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = get_settings(request.user)

        if 'save' in request.POST:
            form = self.form_class(request.POST, instance=self.object)

            if form.is_valid():
                form.save()

            else:
                messages.error(request, "Invalid input")

        return HttpResponseRedirect(self.request.path_info)

# Create your views here.
class ChannelView(ViewMixin, generic.ListView):
    model = Channel
    template_name = 'forumapp/channel.html'

    form_class = ChannelForm

    queryset = Channel.objects
    context_object_name = 'channel_list'

    def get_object(self, exclude=None):
        return self.queryset.all()

    def post(self, request, *args, **kwargs):

        if 'add_favorite' in request.POST:
            settings = get_settings(self.request.user)
            favs = json.loads(settings.favorites)
            channel_name = request.POST['channel_name']

            if not channel_name in favs:
                favs.append(channel_name)
                settings.favorites = json.dumps(favs)
                settings.save()
            else:
                messages.error(request, "Channel already in favorites")

        elif 'remove_favorite' in request.POST:
            settings = get_settings(self.request.user)
            favs = json.loads(settings.favorites)
            channel_name = request.POST['channel_name']
            
            if channel_name in favs:
                favs.remove(channel_name)
                settings.favorites = json.dumps(favs)
                settings.save()
            else:
                messages.error(request, "Channel not found in favorites")        

        elif 'create' in request.POST:
            try:
                owner = request.user
                channel = Channel(owner=owner)
                form = self.form_class(request.POST, instance=channel)

            except ValueError:
                messages.error(request, "Please log in to create channels.")
                return HttpResponseRedirect(self.request.path_info)

            if form.is_valid():
                channel_name = form.cleaned_data.get('channel_name')
                description = form.cleaned_data.get('description')

                if len(channel_name) > 3:
                    if len(description) > 5:

                        channel.save()
                        return HttpResponseRedirect(reverse('forumapp:thread', kwargs={'channel': channel_name}))

                    else:
                        channel.delete()
                        messages.error(request, "Channel description must be at least 6 characters.")

                else:
                    channel.delete()
                    messages.error(request, "Channel name must be at least 4 characters.")

            elif Channel.objects.filter(channel_name=form. data.get('channel_name')).exists():
                messages.error(request, "Channel already exists with that name.")

            else:
                channel.delete()
                messages.error(request, "Invalid input. Channel name must contain hyphens in place of whitespace and cannot contain symbols.")

        return HttpResponseRedirect(self.request.path_info)

class ThreadView(ViewMixin, generic.DetailView):
    model = Thread
    template_name = 'forumapp/thread.html'

    form_class = ThreadForm

    queryset = Thread.objects
    context_object_name = 'thread_list'

    # Return querylist of threads in the given channel
    def get_object(self):
        c_name = self.kwargs.get('channel')

        return self.queryset.filter(channel__channel_name=c_name)

    def post(self, request, *args, **kwargs):
        channel = get_object_or_404(Channel, channel_name=self.kwargs.get('channel'))

        if 'delete' in request.POST:
            channel.delete()

            return HttpResponseRedirect(reverse('forumapp:channel'))

        elif 'back' in request.POST:
            return HttpResponseRedirect(reverse('forumapp:channel'))

        elif 'create' in request.POST:
            try:
                owner = request.user
                thread = Thread(channel=channel, owner=owner)
                thread.save()
                form = self.form_class(request.POST, instance=thread)

            except ValueError:
                messages.error(request, "Please log in to create threads.")
                return HttpResponseRedirect(self.request.path_info)

            if form.is_valid():
                thread_name = form.cleaned_data.get('thread_name')
                description = form.cleaned_data.get('description')

                if len(thread_name) > 5:

                    if len(description) > 5:

                        form.save()

                        #Update recent_date of the channel
                        date = timezone.now()
                        channel.recent_date = date
                        channel.save()

                        return HttpResponseRedirect(reverse('forumapp:comment', kwargs={'channel': channel.channel_name, 'thread': thread.thread_id}))

                    else:
                        thread.delete()
                        messages.error(request, "Thread description must be at least 6 characters.")

                else:
                    thread.delete()
                    messages.error(request, "Thread name must be at least 6 characters.")

            elif Thread.objects.filter(channel=channel, thread_name=form.data.get('thread_name')).exists():
                messages.error(request, "Thread already exists with that name.")

            else:
                thread.delete()
                messages.error(request, "Invalid input")

            return HttpResponseRedirect(self.request.path_info)

class CommentView(ViewMixin, generic.DetailView):
    model = Comment
    template_name = 'forumapp/comment.html'

    form_class = CommentForm

    queryset = Comment.objects
    context_object_name = 'comment_list'

    # Return querylist of comments in the given channel and thread
    def get_object(self):
        t_id = self.kwargs.get('thread')
        c_name = self.kwargs.get('channel')

        return self.queryset.filter(thread__thread_id=t_id, thread__channel__channel_name=c_name)

    def post(self, request, *args, **kwargs):
        thread = get_object_or_404(Thread, channel__channel_name=self.kwargs.get('channel'), thread_id=self.kwargs.get('thread'))

        if 'delete' in request.POST:
            thread.delete()

            return HttpResponseRedirect(reverse('forumapp:thread', kwargs={'channel': self.kwargs.get('channel')}))

        elif 'back' in request.POST:
            return HttpResponseRedirect(reverse('forumapp:thread', kwargs={'channel': self.kwargs.get('channel')}))

        elif 'create' in request.POST:
            try:
                owner = request.user
                comment = Comment(thread=thread, owner=owner)
                comment.save()
                form = self.form_class(request.POST, instance=comment)

            except ValueError:
                messages.error(request, "Please log in to create comments.")
                return HttpResponseRedirect(self.request.path_info)

            if form.is_valid():
                text = form.cleaned_data.get('text')

                if len(text) > 5:

                    form.save()

                    #Update recent_date of the channel and thread
                    date = timezone.now()
                    thread.channel.recent_date = date
                    thread.channel.save()

                    thread.recent_date = date
                    thread.save()

                    return HttpResponseRedirect(self.request.path_info)

                else:
                    comment.delete()
                    messages.error(request, "Comments must be at least 6 characters.")

            else:
                comment.delete()
                messages.error(request, "Invalid input.")

            return HttpResponseRedirect(self.request.path_info)

class UserView(ViewMixin, generic.DetailView):
    model = User
    template_name = 'forumapp/user.html'

    queryset = User.objects
    def get_object(self):
        username = self.kwargs.get('username')
        if self.queryset.filter(username=username).exists():
            return self.queryset.get(username=username)

        return self.queryset.none()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UserView, self).get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        username = self.kwargs.get('username')
        if 'admin_ban' in request.POST:
            user = self.queryset.filter(username=username)
            if user.exists():
                user = user.get()
                user.is_active = False
                user.save()
                return HttpResponseRedirect(self.request.path_info)
            else:
                return Http404("User does not exist.")

        elif 'admin_unban' in request.POST:
            user = self.queryset.filter(username=username)
            if user.exists():

                user = user.get()
                user.is_active = True
                user.save()
                return HttpResponseRedirect(self.request.path_info)
            else:
                return Http404("User does not exist.")

        elif 'owner_ban' in request.POST:
            user = self.queryset.filter(username=username)
            if user.exists():

                channel_name = request.POST.get('owner_ban').replace(' ', '-')
                channel = Channel.objects.filter(channel_name=channel_name)
                if channel.exists():

                    channel = channel.get()
                    list = json.loads(channel.banned_users)
                    list.append(username)
                    channel.banned_users = json.dumps(list)
                    channel.save()
                    return HttpResponseRedirect(self.request.path_info)

                else:
                    return Http404("Couldn't find that channel.")

            else:
                return Http404("User does not exist.")

        elif 'owner_unban' in request.POST:
            user = self.queryset.filter(username=username)
            if user.exists():

                channel_name = request.POST.get('owner_unban').replace(' ', '-')
                channel = Channel.objects.filter(channel_name=channel_name)
                if channel.exists():

                    channel = channel.get()
                    list = json.loads(channel.banned_users)
                    for i in range(len(list)):
                        if username in list[i]:
                            list.pop(i)
                    print(list)
                    channel.banned_users = json.dumps(list)
                    channel.save()
                    return HttpResponseRedirect(self.request.path_info)

                else:
                    return Http404("Couldn't find that channel.")

            else:
                return Http404("User does not exist.")

        elif 'moderator_ban' in request.POST:
            user = self.queryset.filter(username=username)
            if user.exists():

                channel_name = request.POST.get('moderator_ban').replace(' ', '-')
                channel = Channel.objects.filter(channel_name=channel_name)
                if channel.exists():

                    channel = channel.get()
                    list = json.loads(channel.banned_users)
                    list.append(username)
                    channel.banned_users = json.dumps(list)
                    channel.save()
                    return HttpResponseRedirect(self.request.path_info)

                else:
                    return Http404("Couldn't find that channel.")

            else:
                return Http404("User does not exist.")

        elif 'moderator_unban' in request.POST:
            user = self.queryset.filter(username=username)
            if user.exists():

                channel_name = request.POST.get('moderator_unban').replace(' ', '-')
                channel = Channel.objects.filter(channel_name=channel_name)
                if channel.exists():

                    channel = channel.get()
                    list = json.loads(channel.banned_users)
                    for i in range(len(list)):
                        if username in list[i]:
                            list.pop(i)
                    print(list)
                    channel.banned_users = json.dumps(list)
                    channel.save()
                    return HttpResponseRedirect(self.request.path_info)

                else:
                    return Http404("Couldn't find that channel.")

            else:
                return Http404("User does not exist.")

class FavoritesView(ViewMixin, generic.DetailView):
    model = Channel
    template_name = 'forumapp/favorites.html'

    queryset = Channel.objects
    context_object_name = 'favorites_list'

    def get_object(self):
        if self.request.user.is_authenticated():
            settings = get_settings(self.request.user)
            return self.queryset.filter(channel_name__in=json.loads(settings.favorites))
        
        return self.queryset.none()

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('forumapp:channel'))

        if 'add_favorite' in request.POST:
            settings = get_settings(self.request.user)
            favs = json.loads(settings.favorites)
            channel_name = request.POST['channel_name']

            if not channel_name in favs:
                favs.append(channel_name)
                settings.favorites = json.dumps(favs)
                settings.save()
    
            else:
                messages.error(request, "Channel already in favorites")

        elif 'remove_favorite' in request.POST:
            settings = get_settings(self.request.user)
            favs = json.loads(settings.favorites)
            channel_name = request.POST['channel_name']
            
            if channel_name in favs:
                favs.remove(channel_name)
                settings.favorites = json.dumps(favs)
                settings.save()
            else:
                messages.error(request, "Channel not found in favorites")
        
        return HttpResponseRedirect(self.request.path_info)
