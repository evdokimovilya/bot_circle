from django.contrib import admin

from .models import *
from .telegram_bot import PollSender, bot

@admin.register(ProfileVideoNote)
class ProfileVideoNoteAdmin(admin.ModelAdmin):
    list_display = ('profile', "status", 'created_at')
    readonly_fields = ('created_at',)
    
@admin.register(PublicVideoMessage)
class PublicVideoMessageAdmin(admin.ModelAdmin):
    list_display = ('profile_from', "profile_to", 'video', 'created_at')

@admin.action(description="начать голосование")
def start_poll(modeladmin, request, queryset):
    PollSender(bot).start_poll(queryset[0])

class PollOptionInline(admin.StackedInline):
    model = PollOption
    fields = ('text',)

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    actions = [start_poll]
    list_display = ('question', )
    readonly_fields = ('created_at',)
    inlines = [
        PollOptionInline,
    ]

@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ('text',)
