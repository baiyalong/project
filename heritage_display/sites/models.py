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
