import React from 'react';
import { Navigate } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import LoadingScreen from '../common/LoadingScreen';

const ProtectedRoute = ({ children }) => {
  const { state } = useApp();

  // Show loading screen while checking authentication
  if (state.loading) {
    return <LoadingScreen />;
  }

  // If not authenticated, redirect to landing page
  if (!state.user) {
    return <Navigate to="/auth/" replace />;
  }

  // If authenticated but onboarding not complete, redirect to onboarding
  if (!state.onboardingComplete) {
    return <Navigate to="/auth/onboarding" replace />;
  }

  // If authenticated and onboarding complete, show the protected content
  return children;
};

export default ProtectedRoute;