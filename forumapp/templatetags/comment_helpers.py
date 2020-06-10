import json
from django import template
from forumapp.models import Channel, Thread, Comment

register = template.Library()

#Create filter for comments to check if their publish date is within 24 hours before now.
@register.filter
def is_recent(comment):
    return comment.is_recent()

#Create filter for comments to see if they are owned by the user passed in
@register.filter
def is_owned_by(kwargs, username):
    channel_name = kwargs['channel']
    thread_id = kwargs['thread']
    
    thread = Thread.objects.filter(channel__channel_name=channel_name, thread_id=thread_id)
    if thread.exists():
        return thread.get().owner == user
    else:
        return ''

@register.filter
def get_thread_name(kwargs):
    channel_name = kwargs['channel']
    thread_id = kwargs['thread']
    
    thread = Thread.objects.filter(channel__channel_name=channel_name, thread_id=thread_id)
    if thread.exists():
        return thread.get().thread_name
    else:
        return ''

#Custom filter for comments to return the thread they belong to's description
@register.filter
def description(kwargs):
    channel_name = kwargs['channel']
    thread_id = kwargs['thread']
    
    thread = Thread.objects.filter(channel__channel_name=channel_name, thread_id=thread_id)
    if thread.exists():
        return thread.get().description
    else:
        return ''

@register.filter
def is_moderator(kwargs, user):
    channel_name = kwargs['channel']
    thread_id = kwargs['thread']

    thread = Thread.objects.filter(channel__channel_name=channel_name, thread_id=thread_id)
    if thread.exists():
        thread = thread.get()
        if user == thread.channel.owner:
            return True
        else:
            return user.get_username() in json.loads(thread.channel.moderators)

    return False
