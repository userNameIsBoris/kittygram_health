from django.urls import include, path

from cats.views import cat_list

urlpatterns = [
   path('cats/', cat_list),
   path('api/', include('health.urls')),
]


