// Crawler trigger and progress display logic
let currentTaskId = null;
let pollInterval = null;

// Get CSRF Token
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Helper to handle fetch responses safely
function handleFetchResponse(response) {
    if (response.redirected && response.url.includes('login')) {
        alert('Session expired. Please log in again.');
        window.location.reload(); // Will redirect to login
        throw new Error('Session expired');
    }

    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
        // Received HTML (likely login page) but not via redirect
        alert('Authentication required. Reloading...');
        window.location.reload();
        throw new Error('Authentication required');
    }

    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }

    return response.json();
}

// Helper to toggle buttons
function toggleCrawlButtons(isRunning) {
    const btnFull = document.getElementById('btn-start-full-crawl');
    const btnStop = document.getElementById('btn-stop-crawl');

    if (isRunning) {
        if (btnFull) btnFull.style.display = 'none';
        if (btnStop) btnStop.style.display = 'block';
    } else {
        if (btnFull) {
            btnFull.style.display = 'block';
            btnFull.disabled = false;
        }
        if (btnStop) btnStop.style.display = 'none';
    }
}

// Start full crawl
document.addEventListener('DOMContentLoaded', function () {
    const btnFullCrawl = document.getElementById('btn-start-full-crawl');

    // Check for existing active task on load
    if (btnFullCrawl) {
        fetch('/crawl/active-full/')
            .then(res => res.json())
            .then(data => {
                if (data.task_id && (data.status === 'running' || data.status === 'pending')) {
                    currentTaskId = data.task_id;
                    document.getElementById('total-progress').style.display = 'block';
                    toggleCrawlButtons(true);
                    startPolling();
                } else {
                    toggleCrawlButtons(false);
                }
            })
            .catch(console.error);
    }

    if (btnFullCrawl) {
        btnFullCrawl.addEventListener('click', function () {
            // Confirmation removed
            fetch('/crawl/start-full/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            })
                .then(handleFetchResponse)
                .then(data => {
                    currentTaskId = data.task_id;
                    document.getElementById('total-progress').style.display = 'block';
                    toggleCrawlButtons(true);
                    startPolling();
                })
                .catch(err => {
                    if (err.message !== 'Session expired' && err.message !== 'Authentication required') {
                        alert('Failed to start: ' + err.message);
                    }
                    toggleCrawlButtons(false);
                });
        });
    }

    // Stop all crawls
    const btnStopCrawl = document.getElementById('btn-stop-crawl');
    if (btnStopCrawl) {
        btnStopCrawl.addEventListener('click', function () {
            // Confirmation removed
            fetch('/crawl/stop-all/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'stopped') {
                        // Reset UI
                        if (pollInterval) clearInterval(pollInterval);
                        document.getElementById('total-progress').style.display = 'none';
                        toggleCrawlButtons(false);
                        alert('All tasks stopped.');
                        location.reload();
                    }
                })
                .catch(err => {
                    alert('Error stopping: ' + err);
                    toggleCrawlButtons(false);
                });
        });
    }

    // Start single update
    document.querySelectorAll('.btn-update-single').forEach(btn => {
        btn.addEventListener('click', function () {
            const siteId = this.dataset.siteId;
            const siteName = this.dataset.siteName;

            // Confirmation removed
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Qué...';

            // Immediately show progress container
            const row = this.closest('tr');
            if (row) {
                const progressDiv = row.querySelector('.item-progress');
                if (progressDiv) {
                    progressDiv.style.display = 'block';
                    progressDiv.querySelector('small').textContent = 'Queuing task...';
                }
            }

            fetch(`/crawl/start-single/${siteId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
                .then(handleFetchResponse)
                .then(data => {
                    currentTaskId = data.task_id;
                    // Update UI to show it's queued/running
                    if (row) {
                        const progressDiv = row.querySelector('.item-progress');
                        if (progressDiv) {
                            progressDiv.querySelector('small').textContent = 'Task queued (ID: ' + currentTaskId + ')';
                        }
                    }
                    // For single task, we don't necessarily toggle the global buttons, 
                    // unless you want "Stop" to stop single tasks too. 
                    // Assuming "Stop & Clear" is for the global queue.
                    startPolling();
                })
                .catch(err => {
                    this.disabled = false;
                    this.innerHTML = '<i class="bi bi-arrow-repeat"></i> Update';
                    if (err.message !== 'Session expired' && err.message !== 'Authentication required') {
                        alert('Failed to start: ' + err.message);
                    }
                });
        });
    });
});



// Poll task status
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(() => {
        fetch(`/crawl/status/${currentTaskId}/`)
            .then(res => {
                // Poll requests might also fail if session dies mid-crawl
                if (!res.ok) return null;
                return res.json();
            })
            .then(data => {
                if (!data) return; // Skip if error

                updateProgress(data);

                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);

                    // Reset buttons
                    const btnFull = document.getElementById('btn-start-full-crawl');
                    const btnStop = document.getElementById('btn-stop-crawl');
                    if (btnFull) btnFull.style.display = 'block';
                    if (btnStop) btnStop.style.display = 'none';
                    if (btnFull) btnFull.disabled = false;

                    if (data.status === 'completed') {
                        // Silent refresh
                        setTimeout(() => location.reload(), 500);
                    } else {
                        console.error('Crawling failed');
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

            // Normalize strings for comparison
            const normSiteName = siteName ? siteName.trim() : '';
            const normCurrentItem = data.current_item.trim();

            if (normSiteName === normCurrentItem) {
                el.style.display = 'block';
                const progressBar = el.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = '100%'; // Show full bar or animated
                    progressBar.classList.add('progress-bar-animated');
                }
                const statusText = el.querySelector('small');
                if (statusText) statusText.innerHTML = '<i class="bi bi-arrow-repeat spin"></i> Updating...';
            } else {
                // For full crawl, we hide others to avoid clutter, 
                // OR we could check if it WAS just updated (harder without state)
                // For now, only show active one
                el.style.display = 'none';
            }
        });
    }
}
