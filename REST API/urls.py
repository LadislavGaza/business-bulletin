from django.urls import path

from . import uptimeprogram, submisprogram, companiesprogram, submisv2, companiesv2

urlpatterns = [
    path('v1/health/', uptimeprogram.uptime_db, name='index'),
    path('v1/ov/submissions/', submisprogram.krizovatka, name='index'),
    path('v1/ov/submissions/<str:id>', submisprogram.delete_metoda, name='index'),
    path('v1/companies/', companiesprogram.krizovatka, name='index'),

    path('v2/ov/submissions/', submisv2.krizovatka, name='index'),
    path('v2/ov/submissions/<str:reqid>', submisv2.dvojkrizovatka, name='index'),
    path('v2/companies/', companiesv2.krizovatka, name='index'),
]