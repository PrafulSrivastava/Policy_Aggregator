# Policy Aggregator Frontend

React-based admin interface for the Policy Aggregator application.

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router v7** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first CSS framework
- **Vitest** - Testing framework

## Design System

The frontend implements the **Minimalist Monochrome** design system:
- Pure black (#000000) and white (#FFFFFF) palette
- Serif typography (Playfair Display for headlines, Source Serif 4 for body)
- Sharp 90-degree corners (no border-radius)
- Line-based visual system
- Dramatic negative space
- Instant transitions (0-100ms)

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page components
│   ├── services/       # API client services
│   ├── contexts/        # React contexts
│   ├── hooks/          # Custom React hooks
│   ├── utils/           # Utility functions
│   ├── test/            # Test setup
│   └── __tests__/       # Unit tests
├── public/              # Static assets
└── package.json
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
npm install
```

### Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

Build for production:

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Testing

Run unit tests:

```bash
npm test
```

Run tests with UI:

```bash
npm run test:ui
```

## Authentication

The frontend implements JWT-based authentication:

1. **Login**: Users log in via `/login` with username and password
2. **Token Storage**: JWT tokens are stored in localStorage
3. **Protected Routes**: All routes except `/login` require authentication
4. **Auto-redirect**: Unauthenticated users are redirected to login
5. **Session Persistence**: Tokens are validated on app load

## API Integration

The frontend communicates with the FastAPI backend:

- **Base URL**: Configured via `VITE_API_BASE_URL` environment variable
- **Authentication**: Bearer token in `Authorization` header
- **Error Handling**: 401 errors automatically redirect to login
- **CORS**: Backend must allow requests from frontend origin

## Available Routes

- `/login` - Login page (public)
- `/` - Dashboard (protected)
- `/routes` - Route subscriptions (protected)
- `/sources` - Policy sources (protected)
- `/changes` - Policy changes (protected)

## Development Notes

- The frontend uses TypeScript for type safety
- All API calls go through the `apiClient` service
- Authentication state is managed via `AuthContext`
- Protected routes use the `ProtectedRoute` component wrapper
- Design system styles are in `src/index.css` with Tailwind utilities
