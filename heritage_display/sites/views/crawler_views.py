"""
Crawler control views for triggering and monitoring crawl tasks
"""
import subprocess
import os
import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from ..models import HeritageSite, CrawlTask

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def start_full_crawl(request):
    """Start full crawl of all heritage sites"""
    try:
        task = CrawlTask.objects.create(task_type='full', status='pending')
        
        # Get Python interpreter and spider script paths
        python_path = os.path.join(settings.BASE_DIR.parent, '.venv', 'bin', 'python')
        spider_path = os.path.join(settings.BASE_DIR.parent, 'heritage_pipeline', 'run_spider.py')
        
        # Validate paths exist
        if not os.path.exists(python_path):
            raise FileNotFoundError(f"Python interpreter not found: {python_path}")
        if not os.path.exists(spider_path):
            raise FileNotFoundError(f"Spider script not found: {spider_path}")
        
        # Validate task ID (prevent command injection)
        task_id_str = str(task.id)
        if not task_id_str.isdigit():
            raise ValueError("Invalid task ID")
        
        # Start crawler subprocess with error handling
        process = subprocess.Popen(
            [python_path, spider_path, '--task-id', task_id_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        task.status = 'running'
        task.save()
        
        logger.info(f"Started full crawl task {task.id}, process PID: {process.pid}")
        return JsonResponse({'task_id': task.id, 'status': 'started'})
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        return JsonResponse({'error': 'Configuration error', 'detail': str(e)}, status=500)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return JsonResponse({'error': 'Invalid input', 'detail': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error starting crawl: {str(e)}")
        return JsonResponse({'error': 'Internal server error', 'detail': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def start_single_crawl(request, pk):
    """Start single site update crawl"""
    try:
        # Validate pk is integer
        try:
            pk = int(pk)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid site ID'}, status=400)
        
        site = get_object_or_404(HeritageSite, pk=pk)
        url = site.metadata.get('url')
        
        if not url:
            logger.warning(f"No URL found for site {pk}")
            return JsonResponse({'error': 'No URL found for this site'}, status=400)
        
        # Validate URL format (basic check)
        if not url.startswith('http'):
            return JsonResponse({'error': 'Invalid URL format'}, status=400)
        
        task = CrawlTask.objects.create(
            task_type='single',
            target_url=url,
            status='pending',
            total_items=1
        )
        
        # Get paths
        python_path = os.path.join(settings.BASE_DIR.parent, '.venv', 'bin', 'python')
        spider_path = os.path.join(settings.BASE_DIR.parent, 'heritage_pipeline', 'run_spider.py')
        
        # Validate paths
        if not os.path.exists(python_path) or not os.path.exists(spider_path):
            raise FileNotFoundError("Required files not found")
        
        # Validate inputs (prevent command injection)
        task_id_str = str(task.id)
        if not task_id_str.isdigit():
            raise ValueError("Invalid task ID")
        
        # Start subprocess
        process = subprocess.Popen(
            [python_path, spider_path, '--task-id', task_id_str, '--url', url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        task.status = 'running'
        task.save()
        
        logger.info(f"Started single crawl task {task.id} for site {pk}, process PID: {process.pid}")
        return JsonResponse({'task_id': task.id, 'status': 'started'})
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        return JsonResponse({'error': 'Configuration error'}, status=500)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return JsonResponse({'error': 'Invalid input'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error starting single crawl: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


def crawl_status(request, task_id):
    """Query crawl task status (API)"""
    task = get_object_or_404(CrawlTask, pk=task_id)
    return JsonResponse({
        'task_id': task.id,
        'status': task.status,
        'total_items': task.total_items,
        'processed_items': task.processed_items,
        'current_item': task.current_item,
        'current_item_progress': task.current_item_progress,
        'progress_percentage': task.progress_percentage,
    })
