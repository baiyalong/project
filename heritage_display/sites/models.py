from django.db import models

class HeritageSite(models.Model):
    """世界遗产模型 - 映射现有表"""
    name = models.CharField(max_length=255, verbose_name='名称')
    country = models.CharField(max_length=100, verbose_name='国家')
    description_en = models.TextField(verbose_name='英文描述')
    description_zh = models.TextField(blank=True, verbose_name='中文描述')
    content = models.TextField(verbose_name='详细内容')
    category = models.CharField(max_length=50, verbose_name='类型')
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'heritage_site'
        managed = False  # 不让 Django 管理表结构,使用现有表
        verbose_name = '世界遗产'
        verbose_name_plural = '世界遗产'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class CrawlTask(models.Model):
    """爬取任务模型"""
    TASK_TYPE_CHOICES = [
        ('full', '全量爬取'),
        ('single', '单条更新'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')
    target_url = models.URLField(null=True, blank=True, verbose_name='目标URL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    total_items = models.IntegerField(default=0, verbose_name='总条目数')
    processed_items = models.IntegerField(default=0, verbose_name='已处理数')
    current_item = models.CharField(max_length=255, blank=True, verbose_name='当前处理项')
    current_item_progress = models.IntegerField(default=0, verbose_name='当前项进度')  # 0-100
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    class Meta:
        db_table = 'crawl_task'
        verbose_name = '爬取任务'
        verbose_name_plural = '爬取任务'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.get_status_display()}"
    
    @property
    def progress_percentage(self):
        """计算进度百分比"""
        if self.total_items == 0:
            return 0
        return int((self.processed_items / self.total_items) * 100)
