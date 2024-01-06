from django.contrib import admin

from .models import Satellite, Location, Image, Observation

admin.site.register(Satellite)
admin.site.register(Location)
admin.site.register(Image)
admin.site.register(Observation)