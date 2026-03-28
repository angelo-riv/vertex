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
import useDemoControls from './hooks/useDemoControls';
import './styles/globals.css';
import './App.css';

// Inner component so hooks can access AppContext
function AppInner() {
  useDemoControls(); // W/A/D keys work on every page

  return (
    <div className="App">
      <Routes>
        <Route path="/auth/*" element={<AuthContainer />} />
        <Route path="/" element={<Navigate to="/auth/" replace />} />
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<HomePage />} />
          <Route path="/session" element={<SessionPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/support" element={<SupportPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/auth/" replace />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <Router>
        <WebSocketProvider>
          <AppInner />
        </WebSocketProvider>
      </Router>
    </AppProvider>
  );
}

export default App;
