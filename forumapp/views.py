from django.contrib import messages
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.views import generic
from django.utils import timezone
from django.urls import reverse
from .models import Channel, Thread, Comment
from .forms import ChannelForm, ThreadForm, CommentForm

class ViewMixin(generic.base.ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(ViewMixin, self).get_context_data(**kwargs)
        context['form'] = self.form_class(initial=self.initial)
        context[self.context_object_name] = self.get_object()
        return context

# Create your views here.
class ChannelView(ViewMixin, generic.ListView):
    model = Channel
    template_name = 'forumapp/channel.html'

    form_class = ChannelForm
    initial = {'key': 'value'}

    queryset = Channel.objects.all()
    context_object_name = 'channel_list'

    def get_object(self):
        return Channel.objects.all()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            channel_name = form.cleaned_data.get('channel_name')
            description = form.cleaned_data.get('description')
            owner = request.user

            channel = Channel(channel_name=channel_name, description=description, owner=owner)

            try:
                channel.validate_unique()
                channel.save()
                return HttpResponseRedirect(reverse('forumapp:thread', kwargs={'channel': channel_name}))
            except:
                messages.error(request, "Channel already exists with that name.")

        return HttpResponseRedirect(reverse('forumapp:channel'))

class ThreadView(ViewMixin, generic.DetailView):
    model = Thread
    template_name = 'forumapp/thread.html'

    form_class = ThreadForm
    initial = {'key': 'value'}

    queryset = Thread.objects.all()
    context_object_name = 'thread_list'

    # Return querylist of threads in the given channel
    def get_object(self):
        c_name = self.kwargs.get('channel')

        return Thread.objects.filter(channel__channel_name=c_name)

    def post(self, request, *args, **kwargs):

        if 'create' in request.POST:
            form = self.form_class(request.POST)
            if form.is_valid():
                channel = Channel.objects.get(channel_name=self.kwargs.get('channel'))
                thread_name = form.cleaned_data.get('thread_name')
                description = form.cleaned_data.get('description')
                owner = request.user

                thread = Thread(channel=channel, thread_name=thread_name, description=description, owner=owner)
                thread.save()

                #Update recent_date of the channel
                date = timezone.now()
                channel.recent_date = date
                channel.save()

                return HttpResponseRedirect(reverse('forumapp:comment', kwargs={'channel': thread.channel.channel_name, 'thread': thread.thread_id}))

        elif 'delete' in request.POST:
            Channel.objects.get(channel_name=self.kwargs.get('channel')).delete()

            return HttpResponseRedirect(reverse('forumapp:channel'))

        elif 'back' in request.POST:
            return HttpResponseRedirect(reverse('forumapp:channel'))

class CommentView(ViewMixin, generic.DetailView):
    model = Comment
    template_name = 'forumapp/comment.html'

    form_class = CommentForm
    initial = {'key': 'value'}

    queryset = Comment.objects.all()
    context_object_name = 'comment_list'

    # Return querylist of comments in the given channel and thread
    def get_object(self):
        t_id = self.kwargs.get('thread')
        c_name = self.kwargs.get('channel')

        return Comment.objects.filter(thread__thread_id=t_id, thread__channel__channel_name=c_name)

    def post(self, request, *args, **kwargs):

        if 'create' in request.POST:
            form = self.form_class(request.POST)
            if form.is_valid():
                thread = Thread.objects.get(channel__channel_name=kwargs.get('channel'), thread_id=kwargs.get('thread'))
                text = form.cleaned_data.get('text')
                owner = request.user

                comment = Comment(thread=thread, text=text, owner=owner)
                comment.save()

                #Update recent_date of the channel and thread
                date = timezone.now()
                thread.channel.recent_date = date
                thread.channel.save()

                thread.recent_date = date
                thread.save()

                return HttpResponseRedirect(reverse('forumapp:comment', kwargs={'channel': thread.channel.channel_name, 'thread': thread.thread_id}))

            else:
                return CommentView.get(self, request, *args, **kwargs)

        elif 'delete' in request.POST:
            Thread.objects.get(thread_id=self.kwargs.get('thread'), channel__channel_name=self.kwargs.get('channel')).delete()
            return HttpResponseRedirect(reverse('forumapp:thread', kwargs={'channel': self.kwargs.get('channel')}))

        elif 'back' in request.POST:
            return HttpResponseRedirect(reverse('forumapp:thread', kwargs={'channel': self.kwargs.get('channel')}))

class UserView(generic.DetailView):
    model = User
    template_name = 'forumapp/user.html'

    context_object_name = "user"

    def get_object(self):
        username = self.kwargs.get('username')
        if User.objects.filter(username=username).exists():
            return User.objects.get(username=username)
        return None
