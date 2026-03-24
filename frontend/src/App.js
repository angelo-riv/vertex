import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import WebSocketProvider from './components/providers/WebSocketProvider';
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
        <WebSocketProvider>
          <div className="App">
            <Routes>
              {/* Authentication Routes */}
              <Route path="/auth/*" element={<AuthContainer />} />
              
              {/* Root redirect */}
              <Route path="/" element={<Navigate to="/auth/" replace />} />
              
              {/* Main Application Routes - single shared layout */}
              <Route element={<MainLayout />}>
                <Route path="/dashboard" element={<HomePage />} />
                <Route path="/session" element={<SessionPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/support" element={<SupportPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
              
              {/* Fallback */}
              <Route path="*" element={<Navigate to="/auth/" replace />} />
            </Routes>
          </div>
        </WebSocketProvider>
      </Router>
    </AppProvider>
  );
}

export default App;
