// Crawler trigger and progress display logic
let currentTaskId = null;
let pollInterval = null;

// Get CSRF Token
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Start full crawl
document.addEventListener('DOMContentLoaded', function () {
    const btnFullCrawl = document.getElementById('btn-start-full-crawl');
    if (btnFullCrawl) {
        btnFullCrawl.addEventListener('click', function () {
            if (confirm('Are you sure you want to refresh all data? This may take a while.')) {
                fetch('/sites/crawl/start-full/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                })
                    .then(res => res.json())
                    .then(data => {
                        currentTaskId = data.task_id;
                        document.getElementById('total-progress').style.display = 'block';
                        btnFullCrawl.disabled = true;
                        startPolling();
                    })
                    .catch(err => {
                        alert('Failed to start: ' + err.message);
                    });
            }
        });
    }

    // Start single update
    document.querySelectorAll('.btn-update-single').forEach(btn => {
        btn.addEventListener('click', function () {
            const siteId = this.dataset.siteId;
            const siteName = this.dataset.siteName;

            if (confirm(`Are you sure you want to update "${siteName}"?`)) {
                this.disabled = true;

                fetch(`/sites/crawl/start-single/${siteId}/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCsrfToken() }
                })
                    .then(res => res.json())
                    .then(data => {
                        currentTaskId = data.task_id;
                        startPolling();
                    })
                    .catch(err => {
                        alert('Failed to start: ' + err.message);
                        this.disabled = false;
                    });
            }
        });
    });
});

// Poll task status
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(() => {
        fetch(`/sites/crawl/status/${currentTaskId}/`)
            .then(res => res.json())
            .then(data => {
                updateProgress(data);

                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);
                    if (data.status === 'completed') {
                        alert('Crawling completed! Page will refresh automatically.');
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        alert('Crawling failed. Please check the logs.');
                        location.reload();
                    }
                }
            })
            .catch(err => {
                console.error('Failed to query progress:', err);
            });
    }, 2000);  // Query every 2 seconds
}

// Update progress display
function updateProgress(data) {
    // Update total progress
    const percentage = data.progress_percentage;
    const totalProgressBar = document.getElementById('total-progress-bar');
    const totalProgressText = document.getElementById('total-progress-text');

    if (totalProgressBar && totalProgressText) {
        totalProgressBar.style.width = percentage + '%';
        totalProgressText.textContent = `${percentage}% (${data.processed_items}/${data.total_items})`;
    }

    // Update current item progress
    if (data.current_item) {
        document.querySelectorAll('.item-progress').forEach(el => {
            const siteName = el.dataset.siteName;
            if (siteName === data.current_item) {
                el.style.display = 'block';
                const progressBar = el.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = data.current_item_progress + '%';
                }
            } else {
                el.style.display = 'none';
            }
        });
    }
}
