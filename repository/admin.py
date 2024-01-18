from django.contrib import admin

from .models import Image, Location, Observation, Satellite

admin.site.register(Satellite)
admin.site.register(Location)
admin.site.register(Image)
admin.site.register(Observation)
