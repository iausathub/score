from django.contrib import admin

from .models import Location, Observation, Satellite

admin.site.register(Satellite)
admin.site.register(Location)
admin.site.register(Observation)
