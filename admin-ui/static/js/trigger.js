/**
 * Manual trigger functionality for Policy Aggregator Admin UI
 */

// In-memory trigger logs (for MVP - could be moved to database later)
const triggerLogs = {};

/**
 * Show loading overlay
 */
function showLoading(text = 'Processing...', subtext = '') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingSubtext').textContent = subtext;
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

/**
 * Update trigger result display
 */
function updateResultDisplay(sourceId, result) {
    const resultCell = document.getElementById(`result-${sourceId}`);
    if (!resultCell) return;
    
    // Clear previous result
    resultCell.innerHTML = '';
    
    if (!result.success) {
        // Failure
        resultCell.innerHTML = `
            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                Failed
            </span>
            <div class="text-xs text-red-600 mt-1 max-w-xs truncate" title="${result.error || 'Unknown error'}">
                ${result.error || 'Unknown error'}
            </div>
        `;
    } else {
        // Success
        const changeDetected = result.changeDetected;
        if (changeDetected) {
            resultCell.innerHTML = `
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Success
                </span>
                <div class="text-xs text-gray-600 mt-1">
                    Change detected: 
                    <a href="/changes/${result.policyChangeId}" class="text-indigo-600 hover:text-indigo-900">
                        View Change
                    </a>
                </div>
            `;
        } else {
            resultCell.innerHTML = `
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Success
                </span>
                <div class="text-xs text-gray-600 mt-1">No changes detected</div>
            `;
        }
    }
    
    // Update last checked timestamp
    const lastCheckedSpan = document.querySelector(`.last-checked-${sourceId}`);
    if (lastCheckedSpan && result.fetchedAt) {
        lastCheckedSpan.textContent = formatTimestamp(result.fetchedAt);
    }
}

/**
 * Trigger fetch for a single source
 */
async function triggerSource(sourceId, sourceName) {
    const button = document.getElementById(`triggerBtn-${sourceId}`);
    if (!button) return;
    
    // Disable button and show loading
    button.disabled = true;
    button.textContent = 'Fetching...';
    button.classList.add('opacity-50', 'cursor-not-allowed');
    
    showLoading(`Fetching ${sourceName}...`, 'This may take a few moments');
    
    try {
        // Call API
        const result = await API.triggerSource(sourceId);
        
        // Store in trigger logs
        triggerLogs[sourceId] = {
            triggeredAt: new Date().toISOString(),
            result: result
        };
        saveTriggerLogs();
        
        // Update display
        updateResultDisplay(sourceId, result);
        
        // Show success message
        showMessage('success', `Successfully triggered fetch for ${sourceName}`);
        
    } catch (error) {
        console.error('Trigger error:', error);
        
        // Update display with error
        const errorResult = {
            success: false,
            error: error.message || 'Failed to trigger fetch'
        };
        updateResultDisplay(sourceId, errorResult);
        
        // Store error in logs
        triggerLogs[sourceId] = {
            triggeredAt: new Date().toISOString(),
            result: errorResult
        };
        saveTriggerLogs();
        
        // Show error message
        showMessage('error', `Failed to trigger fetch for ${sourceName}: ${error.message || 'Unknown error'}`);
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Fetch Now';
        button.classList.remove('opacity-50', 'cursor-not-allowed');
        hideLoading();
    }
}

/**
 * Trigger all active sources sequentially
 */
async function triggerAllSources() {
    const activeSources = Array.from(document.querySelectorAll('.source-row'))
        .filter(row => {
            const button = row.querySelector('button');
            return button && !button.disabled;
        })
        .map(row => ({
            id: row.dataset.sourceId,
            name: row.querySelector('td').textContent.trim()
        }));
    
    if (activeSources.length === 0) {
        showMessage('info', 'No active sources to trigger');
        return;
    }
    
    const confirmMessage = `Trigger fetch for ${activeSources.length} active source(s)?`;
    if (!confirm(confirmMessage)) {
        return;
    }
    
    showLoading(`Triggering ${activeSources.length} sources...`, 'Processing sequentially');
    
    let successCount = 0;
    let failureCount = 0;
    
    for (let i = 0; i < activeSources.length; i++) {
        const source = activeSources[i];
        showLoading(
            `Triggering ${source.name}...`,
            `Source ${i + 1} of ${activeSources.length}`
        );
        
        try {
            const result = await API.triggerSource(source.id);
            
            // Store in trigger logs
            triggerLogs[source.id] = {
                triggeredAt: new Date().toISOString(),
                result: result
            };
            saveTriggerLogs();
            
            // Update display
            updateResultDisplay(source.id, result);
            
            if (result.success) {
                successCount++;
            } else {
                failureCount++;
            }
            
            // Small delay between triggers to avoid overwhelming the server
            if (i < activeSources.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            
        } catch (error) {
            console.error(`Error triggering ${source.name}:`, error);
            failureCount++;
            
            const errorResult = {
                success: false,
                error: error.message || 'Failed to trigger fetch'
            };
            updateResultDisplay(source.id, errorResult);
            
            triggerLogs[source.id] = {
                triggeredAt: new Date().toISOString(),
                result: errorResult
            };
            saveTriggerLogs();
        }
    }
    
    hideLoading();
    
    // Show summary
    const message = `Triggered ${activeSources.length} source(s): ${successCount} succeeded, ${failureCount} failed`;
    showMessage(successCount > 0 ? 'success' : 'error', message);
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

/**
 * Save trigger logs to localStorage
 */
function saveTriggerLogs() {
    try {
        localStorage.setItem('triggerLogs', JSON.stringify(triggerLogs));
    } catch (e) {
        console.error('Error saving trigger logs:', e);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load trigger logs from localStorage if available (persist across page reloads)
    const storedLogs = localStorage.getItem('triggerLogs');
    if (storedLogs) {
        try {
            const logs = JSON.parse(storedLogs);
            Object.assign(triggerLogs, logs);
            
            // Update display for sources with logs
            Object.keys(logs).forEach(sourceId => {
                const log = logs[sourceId];
                if (log.result) {
                    updateResultDisplay(sourceId, log.result);
                }
            });
        } catch (e) {
            console.error('Error loading trigger logs:', e);
        }
    }
});

