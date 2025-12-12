from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import HeritageSite
from .forms import HeritageSiteFilterForm

def site_list(request):
    """遗产列表页"""
    form = HeritageSiteFilterForm(request.GET)
    sites = HeritageSite.objects.all().order_by('-updated_at')  # 按更新时间倒序排列
    
    # 筛选逻辑
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
    
    # 分页
    paginator = Paginator(sites, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_count': sites.count(),
    }
    
    return render(request, 'sites/site_list.html', context)

def site_detail(request, pk):
    """遗产详情页"""
    site = get_object_or_404(HeritageSite, pk=pk)
    
    context = {
        'site': site,
    }
    
    return render(request, 'sites/site_detail.html', context)
