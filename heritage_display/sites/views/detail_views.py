"""
Detail view for heritage sites
"""
from django.shortcuts import render, get_object_or_404
from ..models import HeritageSite


def site_detail(request, pk):
    """Heritage site detail page
    
    Note:
    - description_en, description_zh, content fields have been converted to Markdown using html2text
    - Use markdown_to_html filter in templates for rendering
    """
    site = get_object_or_404(HeritageSite, pk=pk)
    
    context = {
        'site': site,
    }
    
    return render(request, 'sites/site_detail.html', context)
