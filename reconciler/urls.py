# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.reconcile_view, name='home'),  # Redirect root URL to reconcile_view
#     path('reconcile/', views.reconcile_view, name='reconcile'),
#     path('download-template/<str:file_path>/', views.download_template, name='download_template'),
# ]

from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.reconcile_view, name='home'),  # Redirect root URL to reconcile_view
    path('reconcile/', views.reconcile_view, name='reconcile'),
    # re_path(r'^download-template/(?P<file_path>.+)/$', views.download_template, name='download_template'),
    path('download-template/', views.download_template, name='download_template'),
]