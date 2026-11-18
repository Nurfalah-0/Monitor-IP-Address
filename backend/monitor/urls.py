from django.urls import path

from . import views

urlpatterns = [
    path("visitor/", views.record_visitor, name="api-visitor"),
    path("visitors/", views.list_visitors, name="api-visitors"),
]
