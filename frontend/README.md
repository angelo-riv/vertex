# Frontend - Clinical Dashboard

React-based web application providing a clinical dashboard for therapists to monitor Pusher Syndrome patients and configure rehabilitation devices.

## Overview

The clinical dashboard provides:
- Real-time patient monitoring and posture visualization
- Device configuration and threshold adjustment
- Patient progress tracking and analytics
- Therapy session management
- Clinical reporting and data export

## Technology Stack

- **Framework**: React 19.2.4
- **Build Tool**: Create React App (react-scripts 5.0.1)
- **HTTP Client**: Axios 1.13.5
- **Testing**: Jest + React Testing Library
- **Node.js**: 16+ required

## Setup Instructions

### Prerequisites
- Node.js 16 or higher
- npm package manager

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

### Development

**Start development server**
```bash
npm start
```
Opens [http://localhost:3000](http://localhost:3000) in your browser.
The page will reload when you make changes.

**Run tests**
```bash
npm test
```
Launches the test runner in interactive watch mode.

**Build for production**
```bash
npm run build
```
Builds the app for production to the `build` folder.

## Project Structure

```
frontend/
├── public/              # Static assets
│   ├── index.html      # Main HTML template
│   └── ...             # Icons, manifest, etc.
├── src/                # React source code
│   ├── App.js          # Main application component
│   ├── App.css         # Application styles
│   ├── index.js        # React DOM entry point
│   └── ...             # Components and utilities
├── package.json        # Dependencies and scripts
└── README.md          # This file
```

## Planned Features

### Patient Management
- Patient registration and profile management
- Device pairing and configuration
- Therapy session scheduling

### Real-time Monitoring
- Live posture visualization
- Sensor data streaming
- Alert system for concerning patterns

### Analytics Dashboard
- Progress tracking charts
- Recovery trend analysis
- Comparative analytics
- Clinical reporting

### Device Configuration
- Threshold adjustment interface
- Calibration tools
- Feedback intensity settings
- Safety parameter configuration

## Development Guidelines

### Component Structure
- Use functional components with React Hooks
- Implement responsive design for tablet/desktop use
- Follow accessibility guidelines for clinical software
- Use TypeScript for type safety (planned migration)

### API Integration
- Axios for HTTP requests to backend
- Real-time updates via WebSocket (planned)
- Error handling and retry logic
- Loading states and user feedback

### Clinical Considerations
- **User Experience**: Intuitive interface for healthcare professionals
- **Data Visualization**: Clear, actionable insights from patient data
- **Accessibility**: WCAG compliance for inclusive design
- **Performance**: Fast loading for clinical workflow efficiency
- **Security**: Secure handling of patient data

## Testing

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in CI mode
npm test -- --watchAll=false
```

### Testing Strategy
- Unit tests for components and utilities
- Integration tests for API interactions
- End-to-end tests for critical workflows
- Accessibility testing

## Deployment

### Production Build
```bash
npm run build
```

### Deployment Options
- Static hosting (Netlify, Vercel)
- Docker containerization
- Hospital/clinic internal servers
- Cloud platforms (AWS, Azure, GCP)

### Environment Configuration
Create `.env` files for different environments:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## Contributing

1. Follow React best practices and hooks patterns
2. Use ESLint and Prettier for code formatting
3. Write comprehensive tests for new features
4. Document components with PropTypes or TypeScript
5. Consider clinical workflow in UX design

## Medical Device Compliance

- Follow FDA guidelines for medical device software
- Implement audit trails for clinical actions
- Ensure data privacy and HIPAA compliance
- Design for reliability in clinical environments
- Plan for validation and verification testing
