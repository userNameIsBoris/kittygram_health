from django.urls import include, path
from django.contrib import admin

from cats.views import cat_list

urlpatterns = [
   path('admin/', admin.site.urls),
   path('cats/', cat_list),
   path('api/', include('health.urls')),
]


