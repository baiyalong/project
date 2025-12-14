# 爬虫触发与进度展示 - 完整方案总结

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Heritage Display (Django)                 │
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │  列表页/详情页 │ ──▶ │  视图函数     │                     │
│  │  (按钮触发)   │      │  创建任务     │                     │
│  └──────────────┘      └──────┬───────┘                     │
│                                │                              │
│                                ▼                              │
│                        ┌──────────────┐                      │
│                        │  CrawlTask   │                      │
│                        │  (数据库表)   │                      │
│                        └──────┬───────┘                      │
│                                │                              │
│                                ▼                              │
│                        ┌──────────────┐                      │
│                        │  后台进程     │                      │
│                        │  subprocess  │                      │
│                        └──────┬───────┘                      │
└───────────────────────────────┼─────────────────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  Heritage Pipeline (Scrapy)   │
                │                                │
                │  run_spider.py                 │
                │    ├─ 全量模式: 爬取所有      │
                │    └─ 单条模式: 爬取指定URL   │
                │                                │
                │  heritage_spider.py            │
                │    ├─ 支持 url 参数           │
                │    └─ 更新任务进度            │
                └───────────────────────────────┘
```

## 二、核心组件

### 1. 数据模型 (CrawlTask)

```python
class CrawlTask(models.Model):
    task_type = 'full' / 'single'     # 任务类型
    target_url = URL                   # 单条模式的目标
    status = 'pending' / 'running' / 'completed' / 'failed'
    total_items = 整数                 # 总数
    processed_items = 整数             # 已处理
    current_item = 字符串              # 当前项
    started_at = 时间戳
    completed_at = 时间戳
    error_message = 错误信息
```

### 2. 爬虫改造

**heritage_spider.py**:
- 新增 `url` 参数支持
- 新增 `parse_detail_auto()` 方法
- 单URL模式：直接访问详情页
- 全量模式：从列表页开始

**run_spider.py**:
- 封装 Scrapy 调用
- 接收参数：`--task-id`, `--url`
- 后台运行爬虫

### 3. Django 视图（简化方案）

```python
# 启动全量爬取
def start_full_crawl(request):
    task = CrawlTask.objects.create(task_type='full')
    subprocess.Popen(['python', 'run_spider.py', '--task-id', str(task.id)])
    return redirect('crawl_progress', task_id=task.id)

# 启动单条更新
def start_single_crawl(request, pk):
    site = get_object_or_404(HeritageSite, pk=pk)
    task = CrawlTask.objects.create(
        task_type='single',
        target_url=site.metadata.get('url')
    )
    subprocess.Popen([
        'python', 'run_spider.py',
        '--task-id', str(task.id),
        '--url', task.target_url
    ])
    return redirect('crawl_progress', task_id=task.id)

# 进度页面（自动刷新）
def crawl_progress(request, task_id):
    task = get_object_or_404(CrawlTask, pk=task_id)
    return render(request, 'sites/crawl_progress.html', {'task': task})
```

### 4. 前端界面

**列表页** (`site_list.html`):
```html
<!-- 顶部全量爬取按钮 -->
<form method="post" action="{% url 'sites:start_full_crawl' %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-primary">
        🔄 重新爬取所有数据
    </button>
</form>

<!-- 每行单条更新按钮 -->
<form method="post" action="{% url 'sites:start_single_crawl' site.pk %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-sm btn-outline-primary">
        🔄 更新
    </button>
</form>
```

**进度页面** (`crawl_progress.html`):
```html
<!-- 自动刷新：每3秒 -->
<meta http-equiv="refresh" content="3">

<div class="progress">
    <div class="progress-bar" style="width: {{ task.progress_percentage }}%">
        {{ task.progress_percentage }}%
    </div>
</div>

<p>状态: {{ task.get_status_display }}</p>
<p>进度: {{ task.processed_items }} / {{ task.total_items }}</p>
<p>当前: {{ task.current_item }}</p>
```

## 三、工作流程

### 全量爬取流程
1. 用户点击"重新爬取所有数据"
2. Django 创建 CrawlTask (type='full')
3. 后台启动 `run_spider.py --task-id=X`
4. 重定向到进度页面
5. 进度页面每3秒自动刷新
6. 爬虫完成后状态变为 'completed'

### 单条更新流程
1. 用户点击某行的"更新"按钮
2. Django 创建 CrawlTask (type='single', target_url=...)
3. 后台启动 `run_spider.py --task-id=X --url=Y`
4. 重定向到进度页面
5. 爬虫只爬取该URL
6. 完成后更新数据库

## 四、关键特性

✅ **简化设计**: 无需复杂API，使用传统Django视图
✅ **进度追踪**: CrawlTask 模型记录详细进度
✅ **自动刷新**: meta refresh 实现进度实时更新
✅ **后台执行**: subprocess 异步运行爬虫
✅ **双模式**: 支持全量和单条两种模式

## 五、已完成部分

- [x] 爬虫改造（单URL支持）
- [x] run_spider.py 工具
- [x] CrawlTask 模型
- [x] 数据库迁移

## 六、待完成部分

- [ ] Django 视图函数实现
- [ ] URL 路由配置
- [ ] 前端按钮集成
- [ ] 进度页面模板
- [ ] Pipeline 进度更新逻辑
