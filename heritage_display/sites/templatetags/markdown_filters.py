"""
Markdown 模板过滤器
用于将 Markdown 格式文本转换为安全的 HTML
"""

from django import template
from django.utils.safestring import mark_safe
import markdown
from bleach import clean

register = template.Library()

# 允许的 HTML 标签和属性
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'div', 'span'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'div': ['class', 'id'],
    'span': ['class', 'id'],
    '*': ['class'],
}

@register.filter
def markdown_to_html(text):
    """
    将 Markdown 格式的文本转换为 HTML
    
    Args:
        text: Markdown 格式的文本
        
    Returns:
        安全的 HTML 字符串
    """
    if not text:
        return ''
    
    # 转换 Markdown 为 HTML
    html = markdown.markdown(
        text,
        extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.sane_lists',
        ]
    )
    
    # 清理 HTML，只保留安全的标签和属性
    safe_html = clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return mark_safe(safe_html)
