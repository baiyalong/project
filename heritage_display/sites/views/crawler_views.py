"""
Crawler control views for triggering and monitoring crawl tasks
"""
import logging
import json
import redis
import time
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from ..models import HeritageSite, CrawlTask

logger = logging.getLogger(__name__)

# Initialize Redis connection
# Use settings.REDIS_URL if available, else default
redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
# Safely create redis client
try:
    r = redis.from_url(redis_url)
except Exception as e:
    logger.error(f"Failed to initialize Redis connection: {e}")
    r = None

@login_required
@require_http_methods(["POST"])
def start_full_crawl(request):
    """Start full crawl of all heritage sites via Redis queue"""
    if not r:
        return JsonResponse({'error': 'Redis service not available'}, status=503)

    # Check for existing running tasks in DB
    if CrawlTask.objects.filter(status='running', task_type='full').exists():
        return JsonResponse({'error': 'A full crawl task is already running. Please wait for it to finish.'}, status=409)

    try:
        task = CrawlTask.objects.create(task_type='full', status='pending')
        
        # Prepare payload for Scrapy-Redis
        # The spider will read this JSON
        payload = {
            'task_id': task.id,
            'task_type': 'full',
            'url': getattr(settings, 'CRAWLER_START_URL', 'https://whc.unesco.org/en/list/') # Start URL for full crawl
        }
        
        # Push to Redis queue (heritage_spider:start_urls)
        r.lpush('heritage_spider:start_urls', json.dumps(payload))
        
        logger.info(f"Queued full crawl task {task.id} to Redis")
        return JsonResponse({'task_id': task.id, 'status': 'queued'})
        
    except Exception as e:
        logger.error(f"Error queuing full crawl: {str(e)}")
        return JsonResponse({'error': 'Internal server error', 'detail': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def start_single_crawl(request, pk):
    """Start single site update crawl via Redis queue"""
    if not r:
        return JsonResponse({'error': 'Redis service not available'}, status=503)

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
        
        # Prepare payload
        payload = {
            'task_id': task.id,
            'task_type': 'single',
            'url': url
        }
        
        # Push to Redis
        r.lpush('heritage_spider:start_urls', json.dumps(payload))
        
        logger.info(f"Queued single crawl task {task.id} for site {pk} to Redis")
        return JsonResponse({'task_id': task.id, 'status': 'queued'})
        
    except Exception as e:
        logger.error(f"Error queuing single crawl: {str(e)}")
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

def get_active_full_crawl(request):
    """Check if there is a running or pending full crawl task"""
    task = CrawlTask.objects.filter(status__in=['pending', 'running'], task_type='full').first()
    if task:
        return JsonResponse({'task_id': task.id, 'status': task.status})
    return JsonResponse({'task_id': None, 'status': 'idle'})

@login_required
@require_http_methods(["POST"])
def stop_all_crawls(request):
    """Stop running tasks and clear Redis queue"""
    if not r:
        return JsonResponse({'error': 'Redis service not available'}, status=503)

    try:
        # 1. Clear Redis Queues
        # clear start_urls (new tasks)
        r.delete('heritage_spider:start_urls')
        # clear requests (current spider queue)
        r.delete('heritage_spider:requests')
        
        # 2. Mark running tasks as stopped in DB
        CrawlTask.objects.filter(status__in=['pending', 'running']).update(
            status='stopped',
            completed_at=None,
            error_message='Stopped by user'
        )
        
        logger.info("Stopped all crawls and cleared queue")
        return JsonResponse({'status': 'stopped'})
        
    except Exception as e:
        logger.error(f"Error stopping crawls: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def batch_crawl_status(request):
    """
    Query status for multiple tasks at once.
    Expects a JSON body with keys: {'task_ids': [1, 2, 3]}
    Returns a dict: { '1': { 'status': '...', ... }, '2': { ... } }
    """
    try:
        data = json.loads(request.body)
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return JsonResponse({}, status=200)
            
        # Limit batch size to prevent abuse
        if len(task_ids) > 50:
            return JsonResponse({'error': 'Batch size limit exceeded (max 50)'}, status=400)
            
        tasks = CrawlTask.objects.filter(pk__in=task_ids)
        result = {}
        
        for task in tasks:
            result[str(task.id)] = {
                'task_id': task.id,
                'status': task.status,
                'total_items': task.total_items,
                'processed_items': task.processed_items,
                'current_item': task.current_item,
                'progress_percentage': task.progress_percentage,
                # Include target_url or other meta if needed
            }
            
        return JsonResponse(result, safe=False)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in batch_crawl_status: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
