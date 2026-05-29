from django.contrib import admin
from .models import Conference, Track, Speaker, Session, SessionSpeaker, Registration

class TrackInline(admin.TabularInline):
    model = Track
    extra = 1

class SessionSpeakerInline(admin.TabularInline):
    model = SessionSpeaker
    extra = 1

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'starts_at', 'ends_at', 'timezone')
    search_fields = ('name', 'slug')
    list_filter = ('timezone',)
    inlines = [TrackInline]

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'conference', 'color')
    search_fields = ('name',)
    list_filter = ('conference',)

@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'affiliation')
    search_fields = ('name', 'affiliation')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'track', 'starts_at', 'ends_at', 'capacity')
    search_fields = ('title', 'abstract')
    list_filter = ('track__conference', 'track')
    inlines = [SessionSpeakerInline]

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'session', 'status', 'created')
    search_fields = ('user_email',)
    list_filter = ('status',)
