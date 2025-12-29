/**
 * Dashboard filtering functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Populate route filter dropdown
    populateRouteFilter();
    
    // Initialize route filter
    const routeFilter = document.getElementById('routeFilter');
    if (routeFilter) {
        routeFilter.addEventListener('change', handleRouteFilter);
    }
});

/**
 * Populate route filter dropdown with unique routes from dashboard data
 */
function populateRouteFilter() {
    const routeFilter = document.getElementById('routeFilter');
    if (!routeFilter || !dashboardData) return;
    
    const routeSet = new Set();
    
    // Get unique routes from recent changes
    if (dashboardData.recentChanges) {
        dashboardData.recentChanges.forEach(change => {
            if (change.route) {
                routeSet.add(change.route);
            }
        });
    }
    
    // Get unique routes from source health
    if (dashboardData.sourceHealth) {
        dashboardData.sourceHealth.forEach(source => {
            if (source.country && source.visaType) {
                const route = `${source.country}: ${source.visaType}`;
                routeSet.add(route);
            }
        });
    }
    
    // Get unique routes from route statistics
    if (dashboardData.routeStatistics) {
        dashboardData.routeStatistics.forEach(routeStat => {
            if (routeStat.route) {
                routeSet.add(routeStat.route);
            }
        });
    }
    
    // Populate dropdown
    const sortedRoutes = Array.from(routeSet).sort();
    sortedRoutes.forEach(route => {
        const option = document.createElement('option');
        option.value = route;
        option.textContent = route;
        routeFilter.appendChild(option);
    });
}

/**
 * Handle route filter change
 */
function handleRouteFilter() {
    const routeFilter = document.getElementById('routeFilter');
    if (!routeFilter || !dashboardData) return;
    
    const selectedRoute = routeFilter.value;
    
    // Filter recent changes
    filterRecentChanges(selectedRoute);
    
    // Filter source health
    filterSourceHealth(selectedRoute);
    
    // Filter route statistics
    filterRouteStatistics(selectedRoute);
    
    // Update stats cards (would need server-side filtering for accurate counts)
    // For now, we'll just filter the displayed data
}

/**
 * Filter recent changes table by route
 */
function filterRecentChanges(selectedRoute) {
    const tbody = document.querySelector('.recent-changes-table tbody') || 
                   document.querySelector('table tbody');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        if (row.classList.contains('no-changes-row')) return;
        
        const routeCell = row.querySelector('td:first-child');
        if (!routeCell) return;
        
        const routeText = routeCell.textContent.trim();
        const matches = !selectedRoute || routeText === selectedRoute;
        row.style.display = matches ? '' : 'none';
    });
    
    // Show "no changes" message if all filtered out
    updateNoChangesMessage(tbody, rows);
}

/**
 * Filter source health table by route
 */
function filterSourceHealth(selectedRoute) {
    // Find source health table (second table on page)
    const tables = document.querySelectorAll('table');
    if (tables.length < 2) return;
    
    const sourceHealthTable = tables[1];
    const tbody = sourceHealthTable.querySelector('tbody');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        if (row.classList.contains('no-sources-row')) return;
        
        // Route is in format "Country: VisaType" - check country and visa type columns
        const countryCell = row.querySelector('td:nth-child(2)');
        const visaTypeCell = row.querySelector('td:nth-child(3)');
        
        if (!countryCell || !visaTypeCell) return;
        
        const country = countryCell.textContent.trim();
        const visaType = visaTypeCell.textContent.trim();
        const route = `${country}: ${visaType}`;
        
        const matches = !selectedRoute || route === selectedRoute;
        row.style.display = matches ? '' : 'none';
    });
    
    // Show "no sources" message if all filtered out
    updateNoSourcesMessage(tbody, rows);
}

/**
 * Update "no changes" message visibility
 */
function updateNoChangesMessage(tbody, rows) {
    const visibleRows = Array.from(rows).filter(row => 
        row.style.display !== 'none' && !row.classList.contains('no-changes-row')
    );
    
    let noChangesRow = tbody.querySelector('.no-changes-row');
    
    if (visibleRows.length === 0 && rows.length > 0) {
        if (!noChangesRow) {
            noChangesRow = document.createElement('tr');
            noChangesRow.className = 'no-changes-row';
            noChangesRow.innerHTML = '<td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">No changes match the selected route filter</td>';
            tbody.appendChild(noChangesRow);
        }
    } else {
        if (noChangesRow) {
            noChangesRow.remove();
        }
    }
}

/**
 * Update "no sources" message visibility
 */
function updateNoSourcesMessage(tbody, rows) {
    const visibleRows = Array.from(rows).filter(row => 
        row.style.display !== 'none' && !row.classList.contains('no-sources-row')
    );
    
    let noSourcesRow = tbody.querySelector('.no-sources-row');
    
    if (visibleRows.length === 0 && rows.length > 0) {
        if (!noSourcesRow) {
            noSourcesRow = document.createElement('tr');
            noSourcesRow.className = 'no-sources-row';
            noSourcesRow.innerHTML = '<td colspan="5" class="px-6 py-4 text-center text-sm text-gray-500">No sources match the selected route filter</td>';
            tbody.appendChild(noSourcesRow);
        }
    } else {
        if (noSourcesRow) {
            noSourcesRow.remove();
        }
    }
}

/**
 * Filter route statistics table by route
 */
function filterRouteStatistics(selectedRoute) {
    const routeStatRows = document.querySelectorAll('.route-stat-row');
    if (!routeStatRows.length) return;
    
    routeStatRows.forEach(row => {
        const route = row.getAttribute('data-route');
        const matches = !selectedRoute || route === selectedRoute;
        row.style.display = matches ? '' : 'none';
    });
}

