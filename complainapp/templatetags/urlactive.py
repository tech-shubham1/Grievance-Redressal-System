from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag(takes_context=True)
def navactive(context, url):
    if context['request'].path == reverse(url):
        return 'active'
    return ''