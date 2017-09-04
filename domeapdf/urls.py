"""domeapdf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
  https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
  1. Add an import:  from my_app import views
  2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
  1. Add an import:  from other_app.views import Home
  2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
  1. Import the include() function: from django.conf.urls import url, include
  2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin

from jobmgr import views

urlpatterns = [
  url(r'^admin/', admin.site.urls),
  url(r'^accounts/', include('django.contrib.auth.urls')),
  url(r'^accounts/new$', views.signup, name='signup'),
  url(r'^accounts/activate/(?P<uidb64>[0-9a-zA-Z_-]+)/(?P<token>[0-9a-zA-Z]{1,13}-[0-9a-zA-Z]{1,20})/$', views.activate, name='activate'),
  url(r'^', include('jobmgr.urls')),
]
