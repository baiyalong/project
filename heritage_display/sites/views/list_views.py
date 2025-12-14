"""
List view for heritage sites
"""
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
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
