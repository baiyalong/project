// Crawler trigger and progress display logic
// Refactored to support concurrent tasks and persistence

// State
let currentFullTaskId = null;
// activeSingleTasks: Array of { taskId: number, siteId: number }
let activeSingleTasks = [];
let pollInterval = null;

// Incremental update state
let listUpdateInterval = null;
let lastUpdateTime = null;
let displayedSiteIds = new Set();  // Track which sites are currently displayed

const STORAGE_KEY = 'heritage_active_tasks';

// --- Storage Helpers ---
function loadTasksFromStorage() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            activeSingleTasks = JSON.parse(stored);
        }
    } catch (e) {
        console.error("Failed to load tasks from storage", e);
        activeSingleTasks = [];
    }
}

function saveTasksToStorage() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(activeSingleTasks));
    } catch (e) {
        console.error("Failed to save tasks to storage", e);
    }
}

function addSingleTask(taskId, siteId) {
    // Avoid duplicates
    if (!activeSingleTasks.find(t => t.taskId === taskId)) {
        activeSingleTasks.push({ taskId, siteId });
        saveTasksToStorage();
    }
}

function removeSingleTask(taskId) {
    activeSingleTasks = activeSingleTasks.filter(t => t.taskId !== taskId);
    saveTasksToStorage();
}

// --- Network Helpers ---
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function handleFetchResponse(response) {
    if (response.redirected && response.url.includes('login')) {
        console.warn('Session expired. Reloading...');
        window.location.reload();
        throw new Error('Session expired');
    }

    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
        console.warn('Authentication required. Reloading...');
        window.location.reload();
        throw new Error('Authentication required');
    }

    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }

    return response.json();
}

// --- UI Helpers ---
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

function updateSingleTaskUI(siteId, show, message = '', progress = 100) {
    // Find row by data-site-id
    // We look for .item-progress with data-site-id
    const progressEl = document.querySelector(`.item-progress[data-site-id="${siteId}"]`);
    if (!progressEl) return; // Site might not be on current page

    if (show) {
        progressEl.style.display = 'block';
        if (message) {
            progressEl.querySelector('small').innerHTML = message;
        }
        const bar = progressEl.querySelector('.progress-bar');
        if (bar) {
            bar.style.width = progress + '%';
            if (progress < 100 && progress > 0) {
                bar.classList.add('progress-bar-animated');
            } else if (progress === 100) {
                // Keep animated if we are "updating..."
            }
        }
    } else {
        progressEl.style.display = 'none';
    }
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', function () {
    // 1. Load persisted tasks
    loadTasksFromStorage();

    // 2. Check full crawl status
    const btnFullCrawl = document.getElementById('btn-start-full-crawl');
    if (btnFullCrawl) {
        fetch('/crawl/active-full/')
            .then(res => res.json())
            .then(data => {
                if (data.task_id && (data.status === 'running' || data.status === 'pending')) {
                    currentFullTaskId = data.task_id;
                    document.getElementById('total-progress').style.display = 'block';
                    toggleCrawlButtons(true);
                } else {
                    toggleCrawlButtons(false);
                }
                // Start polling if we have ANY tasks
                checkPolling();
            })
            .catch(console.error);
    } else {
        checkPolling();
    }

    // 3. Bind Full Crawl Button
    if (btnFullCrawl) {
        btnFullCrawl.addEventListener('click', function () {
            fetch('/crawl/start-full/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            })
                .then(handleFetchResponse)
                .then(data => {
                    currentFullTaskId = data.task_id;
                    document.getElementById('total-progress').style.display = 'block';
                    toggleCrawlButtons(true);
                    startListUpdates();  // Start incremental list updates
                    checkPolling();
                })
                .catch(err => {
                    if (err.message !== 'Session expired' && err.message !== 'Authentication required') {
                        console.error('Failed to start full crawl:', err.message);
                    }
                    toggleCrawlButtons(false);
                });
        });
    }

    // 4. Bind Stop Button
    const btnStopCrawl = document.getElementById('btn-stop-crawl');
    if (btnStopCrawl) {
        btnStopCrawl.addEventListener('click', function () {
            fetch('/crawl/stop-all/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'stopped') {
                        // Reset everything
                        currentFullTaskId = null;
                        activeSingleTasks = []; // Clear local tasks
                        saveTasksToStorage();

                        document.getElementById('total-progress').style.display = 'none';
                        toggleCrawlButtons(false);

                        // Hide all single progress bars
                        document.querySelectorAll('.item-progress').forEach(el => el.style.display = 'none');

                        if (pollInterval) clearInterval(pollInterval);
                        stopListUpdates();  // Stop incremental list updates
                        location.reload();
                    }
                })
                .catch(err => {
                    console.error('Error stopping crawl:', err);
                });
        });
    }

    // 5. Bind Single Update Buttons
    document.querySelectorAll('.btn-update-single').forEach(btn => {
        // If this site is already in activeSingleTasks, disable button
        const siteId = parseInt(btn.dataset.siteId);
        if (activeSingleTasks.find(t => t.siteId === siteId)) {
            btn.disabled = true;
            updateSingleTaskUI(siteId, true, '<i class="bi bi-hourglass-split"></i> Resuming...');
        }

        btn.addEventListener('click', function () {
            const siteName = this.dataset.siteName;

            this.disabled = true;
            updateSingleTaskUI(siteId, true, '<span class="spinner-border spinner-border-sm"></span> Queuing...');

            fetch(`/crawl/start-single/${siteId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
                .then(handleFetchResponse)
                .then(data => {
                    const taskId = data.task_id;
                    addSingleTask(taskId, siteId);
                    updateSingleTaskUI(siteId, true, `Task Queued (ID: ${taskId})`);
                    checkPolling();
                })
                .catch(err => {
                    this.disabled = false;
                    updateSingleTaskUI(siteId, false);
                    if (err.message !== 'Session expired' && err.message !== 'Authentication required') {
                        console.error('Failed to start single crawl:', err.message);
                    }
                });
        });
    });
});

// --- Polling Logic ---
function checkPolling() {
    // If we have tasks to poll and no interval, start one
    const hasTasks = (currentFullTaskId !== null) || (activeSingleTasks.length > 0);

    if (hasTasks && !pollInterval) {
        pollInterval = setInterval(pollTasks, 2000);
    } else if (!hasTasks && pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function pollTasks() {
    // Collect all IDs
    const taskIds = [];
    if (currentFullTaskId) taskIds.push(currentFullTaskId);
    activeSingleTasks.forEach(t => taskIds.push(t.taskId));

    if (taskIds.length === 0) {
        checkPolling();
        return;
    }

    fetch('/crawl/status/batch/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ task_ids: taskIds })
    })
        .then(res => {
            if (!res.ok) return null;
            return res.json();
        })
        .then(dataMap => {
            if (!dataMap) return;

            // 1. Update Full Task
            if (currentFullTaskId && dataMap[currentFullTaskId]) {
                const task = dataMap[currentFullTaskId];
                updateFullTaskUI(task);

                if (task.status === 'completed' || task.status === 'failed') {
                    currentFullTaskId = null;
                    // UI cleanup handled inside updateFullTaskUI final check or here
                    setTimeout(() => location.reload(), 1000);
                }
            }

            // 2. Update Single Tasks
            // Iterate backwards to allow removal
            for (let i = activeSingleTasks.length - 1; i >= 0; i--) {
                const { taskId, siteId } = activeSingleTasks[i];
                const task = dataMap[taskId];

                if (task) {
                    // Determine UI state
                    if (task.status === 'pending') {
                        updateSingleTaskUI(siteId, true, '<i class="bi bi-clock"></i> Pending...');
                    } else if (task.status === 'running') {
                        updateSingleTaskUI(siteId, true, '<i class="bi bi-arrow-repeat spin"></i> Updating...');
                    } else if (task.status === 'completed') {
                        updateSingleTaskUI(siteId, true, '<i class="bi bi-check-circle text-success"></i> Done!', 100);
                        // Remove from list
                        removeSingleTask(taskId);
                        // Reload specific row? No easy way, just re-enable button or reload page eventually
                        // For now, let's refresh page after a short delay to see changes, or just leave "Done"
                        // If we don't refresh, the data in table is stale.
                        // Let's reload if it's just a few tasks, or just let user reload?
                        // Better UX: reload page.
                        setTimeout(() => location.reload(), 1000);
                    } else if (task.status === 'failed') {
                        updateSingleTaskUI(siteId, true, '<i class="bi bi-x-circle text-danger"></i> Failed');
                        removeSingleTask(taskId);
                        // Re-enable button
                        const btn = document.querySelector(`.btn-update-single[data-site-id="${siteId}"]`);
                        if (btn) btn.disabled = false;
                    }
                } else {
                    // Task ID not returned? Maybe invalid or cleaned up?
                    // Safety: remove it if not found after some retries?
                    // For now, ignore.
                }
            }

            checkPolling();
        })
        .catch(console.error);
}

function updateFullTaskUI(data) {
    // Update total progress bar
    const percentage = data.progress_percentage;
    const totalProgressBar = document.getElementById('total-progress-bar');
    const totalProgressText = document.getElementById('total-progress-text');

    if (totalProgressBar && totalProgressText) {
        // Format percentage to 2 decimal places
        const formattedPercentage = percentage.toFixed(2);
        totalProgressBar.style.width = percentage + '%';
        totalProgressText.textContent = `${formattedPercentage}% (${data.processed_items}/${data.total_items})`;
    }

    // Optional: Highlight current item in list if visible
    // This is purely visual sugar for "What is currently being crawled"
    // Using name matching here is acceptable for visual flair
    // Reset all highlights first? Expensive.
    // Just highlight current.
    if (data.current_item) {
        const rows = document.querySelectorAll(`[data-site-name="${data.current_item}"]`);
        // We might not find it if pagination is involved.
        // It's fine.
    }
}

// --- Incremental List Update Functions ---
function startListUpdates() {
    if (listUpdateInterval) return;

    // Initialize displayed site IDs from current table
    initializeDisplayedSites();

    // Start polling for updates every 10 seconds
    listUpdateInterval = setInterval(() => {
        fetchAndUpdateList();
    }, 10000);

    // Do an immediate update
    fetchAndUpdateList();
}

function stopListUpdates() {
    if (listUpdateInterval) {
        clearInterval(listUpdateInterval);
        listUpdateInterval = null;
    }
}

function initializeDisplayedSites() {
    displayedSiteIds.clear();
    const rows = document.querySelectorAll('tbody tr[data-site-id]');
    rows.forEach(row => {
        const siteId = parseInt(row.dataset.siteId);
        if (siteId) {
            displayedSiteIds.add(siteId);
        }
    });
}

function fetchAndUpdateList() {
    const params = new URLSearchParams();
    if (lastUpdateTime) {
        params.append('since', lastUpdateTime);
    }
    
    console.log('[List Update] Fetching updates...', lastUpdateTime ? `since ${lastUpdateTime}` : 'initial');
    
    fetch(`/sites/api/updated/?${params}`)
        .then(response => response.json())
        .then(data => {
            console.log('[List Update] Received data:', data);
            
            // Update total count
            updateTotalCount(data.total_count);
            
            // Update list with new/updated sites
            if (data.updated_sites && data.updated_sites.length > 0) {
                console.log(`[List Update] Updating ${data.updated_sites.length} sites`);
                updateSiteRows(data.updated_sites);
            } else {
                console.log('[List Update] No new updates');
            }
            
            // Update last update time
            if (data.server_time) {
                lastUpdateTime = data.server_time;
            }
        })
        .catch(err => {
            console.error('[List Update] Error:', err);
        });
}

function updateTotalCount(count) {
    // Update the total count display
    const countElements = document.querySelectorAll('.total-count, [data-total-count]');
    countElements.forEach(el => {
        el.textContent = count;
    });
}

function updateSiteRows(sites) {
    const tbody = document.querySelector('tbody');
    if (!tbody) return;
    
    // Sort sites by updated_at descending (newest first)
    const sortedSites = sites.sort((a, b) => {
        if (!a.updated_at) return 1;
        if (!b.updated_at) return -1;
        return new Date(b.updated_at) - new Date(a.updated_at);
    });
    
    sortedSites.forEach(site => {
        const existingRow = document.querySelector(`tr[data-site-id="${site.id}"]`);
        
        if (existingRow) {
            // Update existing row and move it to correct position
            updateRow(existingRow, site);
            // Remove and re-insert to maintain sort order
            existingRow.remove();
            insertRowInOrder(tbody, existingRow, site.updated_at);
        } else {
            // Insert new row in correct position based on updated_at
            const newRow = createSiteRow(site);
            insertRowInOrder(tbody, newRow, site.updated_at);
            displayedSiteIds.add(site.id);
            
            // Add a subtle highlight animation
            newRow.classList.add('table-success');
            setTimeout(() => {
                newRow.classList.remove('table-success');
            }, 3000);
        }
    });
}

function insertRowInOrder(tbody, row, updatedAt) {
    if (!updatedAt) {
        tbody.appendChild(row);
        return;
    }
    
    const newDate = new Date(updatedAt);
    const rows = tbody.querySelectorAll('tr[data-site-id]');
    
    // Find the correct position to insert
    let inserted = false;
    for (let i = 0; i < rows.length; i++) {
        const existingRow = rows[i];
        const existingUpdated = existingRow.querySelector('[data-updated-at]');
        
        if (existingUpdated && existingUpdated.textContent) {
            try {
                const existingDate = new Date(existingUpdated.textContent);
                if (newDate > existingDate) {
                    tbody.insertBefore(row, existingRow);
                    inserted = true;
                    break;
                }
            } catch (e) {
                // Skip invalid dates
                continue;
            }
        }
    }
    
    // If not inserted, append to end
    if (!inserted) {
        tbody.appendChild(row);
    }
}

function updateRow(row, site) {
    // Update row data
    row.querySelector('[data-site-name]').textContent = site.name;
    row.querySelector('[data-country]').textContent = site.country;
    row.querySelector('[data-category]').textContent = site.category || '-';

    const updatedCell = row.querySelector('[data-updated-at]');
    if (updatedCell && site.updated_at) {
        const date = new Date(site.updated_at);
        updatedCell.textContent = date.toLocaleString();
    }

    // Add subtle highlight
    row.classList.add('table-info');
    setTimeout(() => {
        row.classList.remove('table-info');
    }, 2000);
}

function createSiteRow(site) {
    const row = document.createElement('tr');
    row.dataset.siteId = site.id;
    row.dataset.siteName = site.name;

    const updatedDate = site.updated_at ? new Date(site.updated_at).toLocaleString() : '-';

    row.innerHTML = `
        <td>${site.id}</td>
        <td data-site-name><a href="/sites/${site.id}/">${site.name}</a></td>
        <td data-country>${site.country}</td>
        <td data-category>${site.category || '-'}</td>
        <td data-updated-at>${updatedDate}</td>
        <td>
            <a href="/sites/${site.id}/" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-eye"></i> View
            </a>
            <button class="btn btn-sm btn-outline-success btn-update-single" 
                    data-site-id="${site.id}" 
                    data-site-name="${site.name}">
                <i class="bi bi-arrow-repeat"></i> Update
            </button>
            <div class="item-progress mt-2" data-site-id="${site.id}" style="display: none;">
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar progress-bar-striped" role="progressbar" style="width: 0%"></div>
                </div>
                <small class="text-muted"></small>
            </div>
        </td>
    `;

    // Bind update button event
    const updateBtn = row.querySelector('.btn-update-single');
    bindSingleUpdateButton(updateBtn);

    return row;
}

function bindSingleUpdateButton(btn) {
    btn.addEventListener('click', function () {
        const siteId = parseInt(this.dataset.siteId);
        const siteName = this.dataset.siteName;

        this.disabled = true;
        updateSingleTaskUI(siteId, true, '<i class="bi bi-hourglass-split"></i> Queuing...');

        fetch(`/sites/crawl/start-single/${siteId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
            .then(handleFetchResponse)
            .then(data => {
                const taskId = data.task_id;
                activeSingleTasks.push({ taskId, siteId });
                saveTasksToStorage();
                updateSingleTaskUI(siteId, true, '<i class="bi bi-arrow-repeat"></i> Updating...');
                checkPolling();
            })
            .catch(err => {
                this.disabled = false;
                updateSingleTaskUI(siteId, false);
                if (err.message !== 'Session expired' && err.message !== 'Authentication required') {
                    console.error('Failed to start single crawl:', err.message);
                }
            });
    });
}

