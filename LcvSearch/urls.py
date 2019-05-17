"""LcvSearch URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
 
from . import view,db
 
urlpatterns = [
    path('', view.index),
    path('search/', view.search),
    path('suggest/', view.suggest),
    path('manage/statistic/', view.get_statistic),
    path('manage/register/', db.register),
    path('manage/login/', db.login),
    path('manage/logout/', db.logout),
    path('manage/userlist/', db.user_list),
    path('manage/patentlist/', view.patent_list),
    path('manage/delete_by_id/', view.delete_by_id),

]
