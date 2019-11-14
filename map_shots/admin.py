from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from map_shots.models import Shot, GeoSquare
from map_shots.tasks import make_combinations, make_shots


class ShotInlineAdmin(admin.TabularInline):
    readonly_fields = ('image', 'created')
    extra = 0
    model = Shot
    classes = ('collapse',)

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-id')

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(GeoSquare)
class GeoSquareAdmin(admin.ModelAdmin):
    inlines = (ShotInlineAdmin,)
    change_form_template = 'admin/geosquare_change.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        response = HttpResponseRedirect(
            reverse('admin:map_shots_geosquare_change', args=(object_id,))
        )

        if request.GET.get('make_shot'):
            make_shots.delay(object_id)
        elif request.GET.get('make_combinations'):
            make_combinations.delay(object_id)
        else:
            response = super().change_view(
                request,
                object_id,
                form_url,
                extra_context
            )

        return response

    def has_delete_permission(self, request, obj=None):
        return False
