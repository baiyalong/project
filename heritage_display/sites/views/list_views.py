"""
List view for heritage sites
"""
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..models import HeritageSite
from ..forms import HeritageSiteFilterForm


def site_list(request):
    """Heritage sites list page with optimized queries"""
    form = HeritageSiteFilterForm(request.GET)
    # Optimize query: only fetch needed fields
    sites = HeritageSite.objects.only(
        'id', 'name', 'country', 'category', 'updated_at', 'metadata'
    ).order_by('-updated_at')
    
    # Filter logic
    if form.is_valid():
        search = form.cleaned_data.get('search')
        country = form.cleaned_data.get('country')
        category = form.cleaned_data.get('category')
        
        if search:
            sites = sites.filter(
                Q(name__icontains=search) | 
                Q(country__icontains=search)
            )
        
        if country:
            sites = sites.filter(country__icontains=country)
        
        if category:
            sites = sites.filter(category=category)
    
    # Pagination
    paginator = Paginator(sites, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_count': sites.count(),
    }
    
    return render(request, 'sites/site_list.html', context)


@require_http_methods(["GET"])
def get_updated_sites(request):
    """获取自指定时间后更新的站点（增量更新）"""
    # 获取客户端最后更新时间
    since = request.GET.get('since')
    
    if since:
        from django.utils.dateparse import parse_datetime
        since_dt = parse_datetime(since)
        if since_dt:
            # 获取在此时间之后更新的站点
            updated_sites = HeritageSite.objects.filter(
                updated_at__gt=since_dt
            ).order_by('-updated_at')[:50]  # 最多返回50个
        else:
            updated_sites = []
    else:
        # 如果没有提供时间，返回最新的20个
        updated_sites = HeritageSite.objects.all().order_by('-updated_at')[:20]
    
    total_count = HeritageSite.objects.count()
    
    sites_data = [{
        'id': site.pk,
        'name': site.name,
        'country': site.country,
        'category': site.category,
        'updated_at': site.updated_at.isoformat() if site.updated_at else None,
    } for site in updated_sites]
    
    return JsonResponse({
        'total_count': total_count,
        'updated_sites': sites_data,
        'server_time': HeritageSite.objects.latest('updated_at').updated_at.isoformat() if HeritageSite.objects.exists() else None,
    })

