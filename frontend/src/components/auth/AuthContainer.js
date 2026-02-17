import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import LandingPage from './LandingPage';
import LoginPage from './LoginPage';
import SignupPage from './SignupPage';
import OnboardingWizard from '../onboarding/OnboardingWizard';
import LoadingScreen from '../common/LoadingScreen';

const AuthContainer = () => {
  const navigate = useNavigate();
  const [initialLoading] = useState(false); // Always false to prevent loading screen

  const handleOnboardingComplete = (assessmentData, calibrationSettings) => {
    // Mark onboarding as complete in localStorage for demo
    localStorage.setItem('onboardingComplete', 'true');
    localStorage.setItem('userEmail', localStorage.getItem('currentUserEmail') || 'test@example.com');
    
    // Navigate to dashboard
    navigate('/dashboard');
  };

  if (initialLoading) {
    return <LoadingScreen />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="login" element={<LoginPage />} />
      <Route path="signup" element={<SignupPage />} />
      <Route 
        path="onboarding" 
        element={<OnboardingWizard onComplete={handleOnboardingComplete} />} 
      />
    </Routes>
  );
};

export default AuthContainer;