/**
 * API client for Policy Aggregator Admin UI
 */

const API = {
    baseURL: '/api',
    
    /**
     * Get authentication headers
     */
    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    },
    
    /**
     * Handle API response
     */
    async handleResponse(response) {
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
            throw new Error(error.detail?.message || error.detail || `HTTP ${response.status}`);
        }
        return response.json();
    },
    
    /**
     * Get all routes
     */
    async getRoutes(page = 1, pageSize = 100) {
        const response = await fetch(`${this.baseURL}/routes?page=${page}&page_size=${pageSize}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    },
    
    /**
     * Get a single route by ID
     */
    async getRoute(routeId) {
        const response = await fetch(`${this.baseURL}/routes/${routeId}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    },
    
    /**
     * Create a new route
     */
    async createRoute(data) {
        const response = await fetch(`${this.baseURL}/routes`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },
    
    /**
     * Update a route
     */
    async updateRoute(routeId, data) {
        const response = await fetch(`${this.baseURL}/routes/${routeId}`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },
    
    /**
     * Delete a route
     */
    async deleteRoute(routeId) {
        const response = await fetch(`${this.baseURL}/routes/${routeId}`, {
            method: 'DELETE',
            headers: this.getHeaders()
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
            throw new Error(error.detail?.message || error.detail || `HTTP ${response.status}`);
        }
        return response.status === 204 ? null : response.json();
    },
    
    /**
     * Get all sources
     */
    async getSources(page = 1, pageSize = 100, filters = {}) {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString(),
            ...filters
        });
        const response = await fetch(`${this.baseURL}/sources?${params}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    },
    
    /**
     * Get a single source by ID
     */
    async getSource(sourceId) {
        const response = await fetch(`${this.baseURL}/sources/${sourceId}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    },
    
    /**
     * Create a new source
     */
    async createSource(data) {
        const response = await fetch(`${this.baseURL}/sources`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },
    
    /**
     * Update a source
     */
    async updateSource(sourceId, data) {
        const response = await fetch(`${this.baseURL}/sources/${sourceId}`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },
    
    /**
     * Delete a source
     */
    async deleteSource(sourceId) {
        const response = await fetch(`${this.baseURL}/sources/${sourceId}`, {
            method: 'DELETE',
            headers: this.getHeaders()
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
            throw new Error(error.detail?.message || error.detail || `HTTP ${response.status}`);
        }
        return response.status === 204 ? null : response.json();
    },
    
    /**
     * Get all changes with filters
     */
    async getChanges(filters = {}) {
        const params = new URLSearchParams({
            page: filters.page || '1',
            page_size: filters.page_size || '50',
            ...(filters.route_id && { route_id: filters.route_id }),
            ...(filters.source_id && { source_id: filters.source_id }),
            ...(filters.start_date && { start_date: filters.start_date }),
            ...(filters.end_date && { end_date: filters.end_date }),
            ...(filters.sort_by && { sort_by: filters.sort_by }),
            ...(filters.sort_order && { sort_order: filters.sort_order })
        });
        const response = await fetch(`${this.baseURL}/changes?${params}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    },
    
    /**
     * Get a single change by ID
     */
    async getChange(changeId) {
        const response = await fetch(`${this.baseURL}/changes/${changeId}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    },
    
    /**
     * Export changes to CSV
     */
    async exportChanges(filters = {}) {
        const params = new URLSearchParams({
            ...(filters.route_id && { route_id: filters.route_id }),
            ...(filters.source_id && { source_id: filters.source_id }),
            ...(filters.start_date && { start_date: filters.start_date }),
            ...(filters.end_date && { end_date: filters.end_date })
        });
        const response = await fetch(`${this.baseURL}/changes/export?${params}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
            throw new Error(error.detail?.message || error.detail || `HTTP ${response.status}`);
        }
        // Download CSV file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `policy_changes_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    },
    
    /**
     * Trigger fetch for a source
     */
    async triggerSource(sourceId) {
        const response = await fetch(`${this.baseURL}/sources/${sourceId}/trigger`, {
            method: 'POST',
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    },
    
    /**
     * Get system status
     */
    async getStatus() {
        const response = await fetch(`${this.baseURL}/status`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    }
};

