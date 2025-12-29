/**
 * System status page functionality
 */

/**
 * Refresh system status
 */
async function refreshStatus() {
    const refreshBtn = document.getElementById('refreshBtnText');
    const refreshSpinner = document.getElementById('refreshSpinner');
    
    // Show loading state
    refreshBtn.textContent = 'Refreshing...';
    refreshSpinner.classList.remove('hidden');
    refreshSpinner.classList.add('animate-spin');
    
    try {
        // Call status API
        const status = await API.getStatus();
        
        // Update statistics
        document.getElementById('totalSources').textContent = status.statistics.total_sources;
        document.getElementById('healthySources').textContent = status.statistics.healthy_sources;
        document.getElementById('errorSources').textContent = status.statistics.error_sources;
        document.getElementById('staleSources').textContent = status.statistics.stale_sources;
        document.getElementById('neverCheckedSources').textContent = status.statistics.never_checked_sources;
        
        // Update last job run
        const lastJobRunEl = document.getElementById('lastJobRun');
        if (lastJobRunEl) {
            if (status.last_daily_job_run) {
                lastJobRunEl.textContent = new Date(status.last_daily_job_run).toLocaleString();
            } else {
                lastJobRunEl.textContent = 'Never run';
            }
        }
        
        // Update sources table
        updateSourcesTable(status.sources);
        
        // Show success message
        showMessage('success', 'Status refreshed successfully');
        
    } catch (error) {
        console.error('Error refreshing status:', error);
        showMessage('error', `Failed to refresh status: ${error.message || 'Unknown error'}`);
    } finally {
        // Reset button state
        refreshBtn.textContent = 'Refresh';
        refreshSpinner.classList.add('hidden');
        refreshSpinner.classList.remove('animate-spin');
    }
}

/**
 * Update sources table with new data
 */
function updateSourcesTable(sources) {
    const tbody = document.getElementById('sourcesTableBody');
    if (!tbody) return;
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    if (sources.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-sm text-gray-500">No sources found</td></tr>';
        return;
    }
    
    // Build new rows
    sources.forEach(source => {
        const row = document.createElement('tr');
        row.className = 'source-row';
        row.dataset.sourceId = source.id;
        
        // Status badge
        let statusBadge = '';
        if (source.status === 'healthy') {
            statusBadge = '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Healthy</span>';
        } else if (source.status === 'error') {
            statusBadge = '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Error</span>';
        } else if (source.status === 'stale') {
            statusBadge = '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Stale</span>';
        } else if (source.status === 'never_checked') {
            statusBadge = '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">Never Checked</span>';
        } else {
            statusBadge = '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">Unknown</span>';
        }
        
        // Error display
        let errorDisplay = '<span class="text-gray-400">-</span>';
        if (source.consecutive_fetch_failures > 0) {
            errorDisplay = `<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">${source.consecutive_fetch_failures}</span>`;
            if (source.last_fetch_error) {
                const errorText = source.last_fetch_error.length > 50 ? source.last_fetch_error.substring(0, 50) + '...' : source.last_fetch_error;
                errorDisplay += `<div class="text-xs text-red-600 mt-1 max-w-xs truncate" title="${source.last_fetch_error}">${errorText}</div>`;
            }
        }
        
        // Format timestamps
        const lastChecked = source.last_checked_at ? new Date(source.last_checked_at).toLocaleString() : 'Never';
        const lastChange = source.last_change_detected_at ? new Date(source.last_change_detected_at).toLocaleString() : '-';
        const nextCheck = source.next_check_time ? new Date(source.next_check_time).toLocaleString() : '-';
        
        // Inactive badge
        const inactiveBadge = !source.is_active ? '<span class="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>' : '';
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                ${source.name}${inactiveBadge}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${source.country} / ${source.visa_type}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
                ${statusBadge}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500" id="lastChecked-${source.id}">
                ${lastChecked}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${lastChange}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${nextCheck}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
                ${errorDisplay}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button 
                    onclick="triggerSource('${source.id}', '${source.name.replace(/'/g, "\\'")}')" 
                    id="triggerBtn-${source.id}"
                    class="bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 text-sm"
                    ${!source.is_active ? 'disabled class="bg-gray-400 cursor-not-allowed"' : ''}
                >
                    Fetch Now
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Trigger fetch for a single source (reuse from trigger.js if available)
 */
async function triggerSource(sourceId, sourceName) {
    // Check if triggerSource function exists from trigger.js
    if (typeof window.triggerSource === 'function') {
        await window.triggerSource(sourceId, sourceName);
        // Refresh status after trigger
        setTimeout(() => refreshStatus(), 1000);
    } else {
        // Fallback: implement basic trigger functionality
        const button = document.getElementById(`triggerBtn-${sourceId}`);
        if (!button) return;
        
        button.disabled = true;
        button.textContent = 'Fetching...';
        button.classList.add('opacity-50', 'cursor-not-allowed');
        
        try {
            const result = await API.triggerSource(sourceId);
            
            // Update last checked timestamp
            const lastCheckedEl = document.getElementById(`lastChecked-${sourceId}`);
            if (lastCheckedEl && result.fetchedAt) {
                lastCheckedEl.textContent = new Date(result.fetchedAt).toLocaleString();
            }
            
            showMessage('success', `Successfully triggered fetch for ${sourceName}`);
            
            // Refresh status after a delay
            setTimeout(() => refreshStatus(), 1000);
            
        } catch (error) {
            console.error('Trigger error:', error);
            showMessage('error', `Failed to trigger fetch for ${sourceName}: ${error.message || 'Unknown error'}`);
        } finally {
            button.disabled = false;
            button.textContent = 'Fetch Now';
            button.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }
}

/**
 * Show message to user
 */
function showMessage(type, message) {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-md shadow-lg max-w-sm ${
        type === 'success' ? 'bg-green-100 text-green-800 border border-green-300' :
        type === 'error' ? 'bg-red-100 text-red-800 border border-red-300' :
        'bg-blue-100 text-blue-800 border border-blue-300'
    }`;
    messageDiv.textContent = message;
    
    // Add to page
    document.body.appendChild(messageDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Auto-refresh every 30 seconds (optional - can be disabled)
let autoRefreshInterval = null;

function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    autoRefreshInterval = setInterval(() => {
        refreshStatus();
    }, 30000); // 30 seconds
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Start auto-refresh (optional - comment out to disable)
    // startAutoRefresh();
    
    // Stop auto-refresh when page is hidden
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            // Optionally restart when page becomes visible
            // startAutoRefresh();
        }
    });
});

