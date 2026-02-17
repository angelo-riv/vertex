import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import AuthContainer from './components/auth/AuthContainer';
import ProtectedRoute from './components/auth/ProtectedRoute';
import MainLayout from './components/layout/MainLayout';
import HomePage from './pages/HomePage';
import SessionPage from './pages/SessionPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SupportPage from './pages/SupportPage';
import SettingsPage from './pages/SettingsPage';
import './styles/globals.css';
import './App.css';

function App() {
  return (
    <AppProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Authentication Routes - should be first to catch /auth paths */}
            <Route path="/auth/*" element={<AuthContainer />} />
            
            {/* Root redirect - redirect to auth landing page */}
            <Route path="/" element={<Navigate to="/auth/" replace />} />
            
            {/* Main Application Routes - Simplified for demo */}
            <Route path="/dashboard" element={<MainLayout />}>
              <Route index element={<HomePage />} />
            </Route>
            
            <Route path="/session" element={<MainLayout />}>
              <Route index element={<SessionPage />} />
            </Route>
            
            <Route path="/analytics" element={<MainLayout />}>
              <Route index element={<AnalyticsPage />} />
            </Route>
            
            <Route path="/support" element={<MainLayout />}>
              <Route index element={<SupportPage />} />
            </Route>
            
            <Route path="/settings" element={<MainLayout />}>
              <Route index element={<SettingsPage />} />
            </Route>
            
            {/* Fallback Route - redirect to landing page */}
            <Route path="*" element={<Navigate to="/auth/" replace />} />
          </Routes>
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;
