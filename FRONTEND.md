# DriftGuardAI Frontend

A modern React (Vite) frontend for DriftGuardAI - the AI Model Governance Platform.

## Features

✅ **Authentication**
- JWT-based login system
- Secure token storage in localStorage
- Protected routes with automatic redirect

✅ **Dashboard**
- View all registered AI models
- Real-time status indicators
- Risk score visualization
- Quick navigation to model details

✅ **Model Management**
- Detailed model information
- Risk score history with Recharts visualization
- Drift metrics monitoring
- Fairness metrics tracking
- Current governance status

✅ **Governance**
- Policy management interface
- Model evaluation against policies
- Deployment approval workflow
- Override capability with justification
- State machine enforcement

✅ **Audit & History**
- Deployment history tracking
- Complete audit trail
- Action logging by user
- Timestamp tracking

## Tech Stack

- **React 19** - UI framework
- **Vite 6** - Build tool
- **React Router 6** - Navigation
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **TypeScript** - Type safety
- **CSS3** - Responsive design

## Setup

### Prerequisites
- Node.js 16+
- Backend API running at `http://localhost:5000`

### Installation

```bash
# Install dependencies
npm install

# Create .env file (copy from .env.example)
cp .env.example .env

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── Common.tsx      # LoadingSpinner, ErrorMessage
│   ├── Navbar.tsx      # Top navigation
│   ├── Sidebar.tsx     # Side navigation
│   ├── ProtectedRoute.tsx
│   └── StatusBadge.tsx
├── pages/              # Page components
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── ModelDetailPage.tsx
│   ├── GovernancePage.tsx
│   └── AuditPage.tsx
├── services/           # API integration
│   └── api.ts          # Axios instance and API calls
├── styles/
│   └── index.css       # Global styles
├── App.tsx             # Main app with routing
└── main.tsx            # Entry point
```

## API Integration

The frontend integrates with the following backend endpoints:

### Authentication
- `POST /auth/login` - User login

### Models
- `GET /models` - List all models
- `GET /models/:id` - Get model details
- `GET /models/:id/drift` - Get drift metrics
- `GET /models/:id/fairness` - Get fairness metrics
- `GET /models/:id/risk-history` - Get risk score history
- `POST /models/:id/deploy` - Deploy model

### Governance
- `GET /governance/policies` - List policies
- `POST /governance/policies` - Create policy
- `PUT /governance/policies/:id` - Update policy
- `POST /governance/evaluate/:modelId` - Evaluate model

### Audit
- `GET /audit/deployments` - Get deployment history
- `GET /audit/trail` - Get audit trail

## Features in Detail

### Login Page
- Email and password authentication
- JWT token storage
- Error handling
- Loading states

### Dashboard
- Grid layout of model cards
- Status badges (Active, Monitoring, Alert)
- Risk score color coding
- Quick action buttons
- Empty state handling

### Model Detail Page
- Comprehensive model information
- Risk score history chart (interactive Recharts)
- Drift metrics table
- Fairness metrics table
- Current governance status
- Deployment controls
- Override modal with justification

### Governance Page
- Policy listing and details
- Model evaluation form
- Evaluation results display
- Violations and recommendations
- Clear governance story

### Audit Trail
- Two-tab interface (Deployments & Audit)
- Sortable tables
- Timestamped records
- Actor tracking
- Detailed action logs

## UI Components

### StatusBadge
- Displays status with color coding
- Supports: active, inactive, monitoring, alert, approved, pending, rejected, success, failed, in_progress

### LoadingSpinner
- Animated loading state
- Clean visual feedback

### ErrorMessage
- Error display with retry capability
- User-friendly messaging

## Styling

The frontend uses a modern, clean design with:
- Responsive grid layouts
- Color-coded status indicators
- Smooth transitions and animations
- Mobile-friendly breakpoints
- Accessibility considerations

## Build

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

## Demo Credentials

Use the credentials provided by your backend:

```
Email: demo@driftguardai.com
Password: [Check backend documentation]
```

## Phase 4 Alignment

This frontend is built specifically for Phase 4 of DriftGuardAI and integrates with:

✅ JWT Authentication
✅ Model Registry
✅ Drift Detection
✅ Fairness Monitoring
✅ Risk Scoring (MRI)
✅ Governance Policy Management
✅ Governance Evaluation
✅ Deployment Control with Override
✅ Audit Trail Logging
✅ Deployment History
✅ Model State Machine Enforcement

## Performance Optimizations

- Lazy component loading via React Router
- Efficient state management
- Memoized expensive calculations
- Optimized re-renders
- Chart library with performance considerations

## Security

- JWT tokens stored in localStorage
- Authorization headers on all API calls
- Protected routes with authentication checks
- Secure override justification handling
- CSRF protection ready

## Contributing

To add new features:

1. Create components in `src/components/`
2. Create pages in `src/pages/`
3. Add API calls to `src/services/api.ts`
4. Add styles to `src/styles/index.css`
5. Follow existing patterns and naming conventions

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## License

MIT

## Support

For issues or questions, check the backend documentation or contact the development team.
