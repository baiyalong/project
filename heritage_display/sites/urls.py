from django.urls import path
from . import views

app_name = 'sites'

urlpatterns = [
    path('', views.site_list, name='list'),
    path('<int:pk>/', views.site_detail, name='detail'),
    
    # 爬虫触发
    path('crawl/start-full/', views.start_full_crawl, name='start_full_crawl'),
    path('crawl/start-single/<int:pk>/', views.start_single_crawl, name='start_single_crawl'),
    path('crawl/status/<int:task_id>/', views.crawl_status, name='crawl_status'),
    path('crawl/active-full/', views.get_active_full_crawl, name='get_active_full_crawl'),
    path('crawl/stop-all/', views.stop_all_crawls, name='stop_all_crawls'),
]
