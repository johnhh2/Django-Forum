from django.conf.urls import url
from django.views.generic import TemplateView

# Test pattern, renders Zurb Foundation default page using base template
app_name = 'foundation'
urlpatterns = [
    url(regex=r'^$',
        view=TemplateView.as_view(template_name="foundation/index.html"),
        name="foundation_index"),

    url(regex=r'^original/$',
        view=TemplateView.as_view(template_name="foundation/original_index.html"),
        name="original_foundation_index"),

    url(regex=r'^scss/$',
        view=TemplateView.as_view(template_name="foundation/scss/index.html"),
        name="foundation_scss_index"),

    url(regex=r'^icons/$',
        view=TemplateView.as_view(template_name="foundation/icons.html"),
        name="foundation_icons"),
]
