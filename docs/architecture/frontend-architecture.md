# Frontend Architecture

This section defines frontend-specific architecture details for the server-rendered admin interface using Jinja2 templates with FastAPI.

### Component Architecture

The frontend uses server-side rendering with Jinja2 templates. Components are organized as reusable template includes and macros, following a simple, utilitarian structure aligned with the "boring is good" principle.

#### Component Organization

```
admin-ui/
├── templates/
│   ├── base.html              # Base template with layout, navigation
│   ├── components/            # Reusable component templates
│   │   ├── button.html        # Button component macro
│   │   ├── form_input.html    # Form input component macro
│   │   ├── table.html         # Table component macro
│   │   ├── modal.html         # Modal/dialog component macro
│   │   ├── status_indicator.html  # Status badge component
│   │   └── alert.html         # Alert/notification component
│   ├── pages/
│   │   ├── login.html         # Login page
│   │   ├── dashboard.html     # Dashboard/home page
│   │   ├── routes/
│   │   │   ├── list.html      # Route subscriptions list
│   │   │   └── form.html      # Add/edit route form
│   │   ├── sources/
│   │   │   ├── list.html      # Sources list
│   │   │   ├── form.html      # Add/edit source form
│   │   │   └── detail.html    # Source status detail
│   │   ├── changes/
│   │   │   ├── list.html      # Change history list
│   │   │   └── detail.html    # Change detail with diff
│   │   └── trigger.html       # Manual trigger/testing page
│   └── emails/                # Email templates (Jinja2)
│       └── change_alert.html   # Policy change email template
└── static/
    ├── css/
    │   └── main.css           # Tailwind CSS (compiled)
    └── js/
        ├── main.js            # Main JavaScript for interactions
        ├── api.js             # API client utilities
        └── forms.js            # Form validation and handling
```

**Component Template Example:**

```jinja2
{# components/button.html #}
{% macro button(text, variant="primary", type="button", disabled=false, loading=false) %}
<button 
    type="{{ type }}"
    class="px-4 py-2 rounded font-medium transition-colors
           {% if variant == 'primary' %}bg-blue-600 text-white hover:bg-blue-700
           {% elif variant == 'secondary' %}bg-gray-200 text-gray-800 hover:bg-gray-300
           {% elif variant == 'danger' %}bg-red-600 text-white hover:bg-red-700
           {% endif %}
           {% if disabled or loading %}opacity-50 cursor-not-allowed{% endif %}"
    {% if disabled or loading %}disabled{% endif %}
>
    {% if loading %}
        <span class="inline-block animate-spin mr-2">⟳</span>
    {% endif %}
    {{ text }}
</button>
{% endmacro %}
```

**Usage in Pages:**

```jinja2
{% from "components/button.html" import button %}

{{ button("Save Route", variant="primary", type="submit") }}
{{ button("Cancel", variant="secondary", type="button") }}
{{ button("Delete", variant="danger", type="button") }}
```

#### Component Template

Base template structure with navigation and layout:

```jinja2
{# base.html #}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Policy Aggregator{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', path='css/main.css') }}">
</head>
<body class="bg-gray-50">
    {% if current_user %}
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between items-center h-16">
                <div class="flex space-x-8">
                    <a href="{{ url_for('dashboard') }}" class="text-gray-700 hover:text-gray-900">Dashboard</a>
                    <a href="{{ url_for('routes_list') }}" class="text-gray-700 hover:text-gray-900">Routes</a>
                    <a href="{{ url_for('sources_list') }}" class="text-gray-700 hover:text-gray-900">Sources</a>
                    <a href="{{ url_for('changes_list') }}" class="text-gray-700 hover:text-gray-900">Changes</a>
                    <a href="{{ url_for('trigger_page') }}" class="text-gray-700 hover:text-gray-900">Trigger</a>
                </div>
                <a href="{{ url_for('logout') }}" class="text-gray-700 hover:text-gray-900">Logout</a>
            </div>
        </div>
    </nav>
    {% endif %}
    
    <main class="max-w-7xl mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>
    
    <script src="{{ url_for('static', path='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### State Management Architecture

Since the frontend uses server-side rendering, state management is primarily server-side. Client-side state is minimal and handled via JavaScript for form interactions and API calls.

#### State Structure

**Server-Side State:**
- User session (JWT token stored in cookie or session)
- Page data (passed from FastAPI routes to Jinja2 templates)
- Form validation errors (rendered server-side)

**Client-Side State:**
- Form input values (handled by browser)
- Loading states (JavaScript-managed for async operations)
- Modal visibility (JavaScript-managed)
- API response caching (optional, minimal for MVP)

**State Management Patterns:**

```javascript
// static/js/main.js
// Minimal client-side state management

// Form state (handled by browser, no framework needed)
// Loading states for async operations
const setLoading = (buttonId, isLoading) => {
    const button = document.getElementById(buttonId);
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '<span class="inline-block animate-spin mr-2">⟳</span> Loading...';
    } else {
        button.disabled = false;
        // Restore original button text
    }
};

// Modal state (simple show/hide)
const showModal = (modalId) => {
    document.getElementById(modalId).classList.remove('hidden');
};

const hideModal = (modalId) => {
    document.getElementById(modalId).classList.add('hidden');
};
```

**No State Management Library Needed:**
- Server-side rendering eliminates need for Redux/Zustand
- Simple JavaScript handles form interactions
- API calls are direct (no complex state synchronization)
- Aligns with "boring is good" principle

### Routing Architecture

FastAPI handles routing server-side. Routes map to Jinja2 template rendering with data from the API layer.

#### Route Organization

**FastAPI Route Structure:**

```python
# api/routes/web.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="admin-ui/templates")

# Dashboard
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, current_user = Depends(get_current_user)):
    # Fetch dashboard data
    stats = await get_dashboard_stats()
    recent_changes = await get_recent_changes(limit=10)
    
    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_changes": recent_changes
    })

# Route Subscriptions
@router.get("/routes", response_class=HTMLResponse)
async def routes_list(request: Request, current_user = Depends(get_current_user)):
    routes = await get_all_routes()
    return templates.TemplateResponse("pages/routes/list.html", {
        "request": request,
        "routes": routes
    })

@router.get("/routes/new", response_class=HTMLResponse)
async def route_form(request: Request, current_user = Depends(get_current_user)):
    return templates.TemplateResponse("pages/routes/form.html", {
        "request": request,
        "route": None  # New route
    })

@router.get("/routes/{id}", response_class=HTMLResponse)
async def route_detail(request: Request, id: str, current_user = Depends(get_current_user)):
    route = await get_route(id)
    return templates.TemplateResponse("pages/routes/form.html", {
        "request": request,
        "route": route  # Edit route
    })

# Similar patterns for sources, changes, trigger pages
```

**Route Structure:**
```
/                    → Dashboard
/login               → Login page
/logout              → Logout (POST)
/routes              → Route subscriptions list
/routes/new          → Create route form
/routes/{id}         → Edit route form
/routes/{id}/delete  → Delete route (POST)
/sources             → Sources list
/sources/new         → Create source form
/sources/{id}        → Source detail/edit
/sources/{id}/trigger → Manual trigger (POST)
/changes             → Change history list
/changes/{id}        → Change detail with diff
/trigger             → Manual trigger page
```

#### Protected Route Pattern

All routes except `/login` and `/health` require authentication:

```python
# api/middleware/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
):
    token = credentials.credentials if credentials else None
    
    # Also check session cookie (for browser-based auth)
    if not token and request:
        token = request.cookies.get("access_token")
    
    if not token:
        # Redirect to login for web requests
        if request and request.headers.get("accept", "").startswith("text/html"):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login", status_code=302)
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate JWT token
    user = validate_jwt_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user
```

### Frontend Services Layer

The frontend communicates with the backend API via JavaScript fetch calls. A simple API client utility handles authentication, error handling, and response parsing.

#### API Client Setup

```javascript
// static/js/api.js
// Simple API client for frontend-backend communication

const API_BASE_URL = window.location.origin; // Same origin for SSR

// Get JWT token from cookie or localStorage
const getAuthToken = () => {
    // Try cookie first (set by server)
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'access_token') {
            return value;
        }
    }
    // Fallback to localStorage (if set by client)
    return localStorage.getItem('access_token');
};

// API request wrapper
const apiRequest = async (endpoint, options = {}) => {
    const token = getAuthToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            // Redirect to login on unauthorized
            window.location.href = '/login';
            return;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Request failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
};

// API methods
const api = {
    // Routes
    getRoutes: () => apiRequest('/routes'),
    createRoute: (data) => apiRequest('/routes', { method: 'POST', body: JSON.stringify(data) }),
    deleteRoute: (id) => apiRequest(`/routes/${id}`, { method: 'DELETE' }),
    
    // Sources
    getSources: (filters) => {
        const params = new URLSearchParams(filters);
        return apiRequest(`/sources?${params}`);
    },
    createSource: (data) => apiRequest('/sources', { method: 'POST', body: JSON.stringify(data) }),
    updateSource: (id, data) => apiRequest(`/sources/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    triggerSource: (id) => apiRequest(`/sources/${id}/trigger`, { method: 'POST' }),
    
    // Changes
    getChanges: (filters) => {
        const params = new URLSearchParams(filters);
        return apiRequest(`/changes?${params}`);
    },
    getChange: (id) => apiRequest(`/changes/${id}`),
    
    // Dashboard
    getDashboard: () => apiRequest('/dashboard')
};

// Export for use in other scripts
window.api = api;
```

#### Service Example

Example usage in a form submission:

```javascript
// static/js/forms.js
// Form handling and validation

document.addEventListener('DOMContentLoaded', () => {
    // Route form submission
    const routeForm = document.getElementById('route-form');
    if (routeForm) {
        routeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(routeForm);
            const data = {
                originCountry: formData.get('origin_country'),
                destinationCountry: formData.get('destination_country'),
                visaType: formData.get('visa_type'),
                email: formData.get('email')
            };
            
            // Client-side validation
            if (!data.originCountry || !data.destinationCountry || !data.visaType || !data.email) {
                showError('All fields are required');
                return;
            }
            
            // Show loading state
            const submitButton = routeForm.querySelector('button[type="submit"]');
            setLoading(submitButton.id, true);
            
            try {
                const routeId = routeForm.dataset.routeId;
                if (routeId) {
                    // Update existing route (if update endpoint exists)
                    await api.updateRoute(routeId, data);
                } else {
                    // Create new route
                    await api.createRoute(data);
                }
                
                // Redirect to routes list on success
                window.location.href = '/routes';
            } catch (error) {
                showError(error.message || 'Failed to save route');
                setLoading(submitButton.id, false);
            }
        });
    }
});

function showError(message) {
    // Display error message to user (simple alert or inline message)
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    } else {
        alert(message); // Fallback
    }
}
```

**Key Design Decisions:**
- **Same-origin API calls:** Frontend and API on same domain (simplifies CORS)
- **JWT token from cookie:** Server sets cookie, JavaScript reads it
- **Simple error handling:** Basic error display, can be enhanced later
- **No complex state management:** Direct API calls, no caching layer needed for MVP
- **Progressive enhancement:** Forms work without JavaScript (server-side validation), JavaScript enhances UX

---
