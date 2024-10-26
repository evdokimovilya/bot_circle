from django.contrib import admin
from django.shortcuts import render, HttpResponseRedirect


from .models import *

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'block_bot', 'nickname']
    search_fields = ["telegram_id", "active", 'block_bot']
    list_filter = ('telegram_id', )