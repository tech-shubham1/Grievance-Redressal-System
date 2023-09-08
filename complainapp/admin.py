from django.contrib import admin

# Register your models here.
from .models import Complain, Profile, Designation, Like

admin.site.register(Complain)
admin.site.register(Profile)
admin.site.register(Designation)
admin.site.register(Like)