import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const LoginPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    
    // Simulate login for now - remove Supabase temporarily
    setTimeout(() => {
      if (formData.email === 'test@example.com' && formData.password === 'password') {
        // Store current user for demo
        localStorage.setItem('currentUserEmail', formData.email);
        
        // Check if user has completed onboarding
        const onboardingComplete = localStorage.getItem('onboardingComplete') === 'true';
        const userEmail = localStorage.getItem('userEmail');
        
        if (onboardingComplete && userEmail === formData.email) {
          // User has completed onboarding before, go to dashboard
          navigate('/dashboard');
        } else {
          // First time login or new user, go to onboarding
          navigate('/auth/onboarding');
        }
      } else {
        setErrors({ general: 'Invalid email or password' });
      }
      setLoading(false);
    }, 1000);
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--primary-blue-50)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--spacing-4)'
    }}>
      <div className="container" style={{ maxWidth: '400px' }}>
        <div className="card">
          {/* Header with Logo */}
          <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-8)' }}>
            <div style={{
              width: '60px',
              height: '60px',
              backgroundColor: 'var(--primary-blue)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto var(--spacing-4)'
            }}>
              <svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" fill="white"/>
              </svg>
            </div>
            <h1 style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: '600',
              color: 'var(--gray-900)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Vertex
            </h1>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)'
            }}>
              Supporting your journey to better balance and posture awareness
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit}>
            {errors.general && (
              <div style={{
                color: 'var(--danger-red)',
                fontSize: 'var(--font-size-sm)',
                marginBottom: 'var(--spacing-4)',
                padding: 'var(--spacing-3)',
                backgroundColor: '#FEF2F2',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #FECACA'
              }}>
                {errors.general}
              </div>
            )}

            <div style={{
              color: 'var(--primary-blue)',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--spacing-4)',
              padding: 'var(--spacing-3)',
              backgroundColor: 'var(--primary-blue-50)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--primary-blue-200)'
            }}>
              Demo: Use email "test@example.com" and password "password" to test login
            </div>

            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                name="email"
                className="form-input"
                placeholder="your-email@example.com"
                value={formData.email}
                onChange={handleInputChange}
                disabled={loading}
                style={{
                  borderColor: errors.email ? 'var(--danger-red)' : undefined
                }}
              />
              {errors.email && (
                <div style={{
                  color: 'var(--danger-red)',
                  fontSize: 'var(--font-size-sm)',
                  marginTop: 'var(--spacing-1)'
                }}>
                  {errors.email}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                className="form-input"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleInputChange}
                disabled={loading}
                style={{
                  borderColor: errors.password ? 'var(--danger-red)' : undefined
                }}
              />
              {errors.password && (
                <div style={{
                  color: 'var(--danger-red)',
                  fontSize: 'var(--font-size-sm)',
                  marginTop: 'var(--spacing-1)'
                }}>
                  {errors.password}
                </div>
              )}
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{
                width: '100%',
                marginBottom: 'var(--spacing-4)',
                opacity: loading ? 0.7 : 1
              }}
            >
              {loading ? 'Signing In...' : 'Log In'}
            </button>
          </form>

          {/* Switch to Signup */}
          <div style={{ textAlign: 'center' }}>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Don't have an account?
            </p>
            <Link
              to="/auth/signup"
              className="btn btn-secondary"
              style={{ 
                width: '100%',
                textDecoration: 'none',
                display: 'inline-block',
                textAlign: 'center',
                marginBottom: 'var(--spacing-3)'
              }}
            >
              Create Account
            </Link>
            
            <Link
              to="/auth/"
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--primary-blue)',
                textDecoration: 'none',
                display: 'block'
              }}
            >
              ← Back to Welcome
            </Link>
          </div>

          {/* Medical Disclaimer */}
          <div style={{
            marginTop: 'var(--spacing-6)',
            padding: 'var(--spacing-4)',
            backgroundColor: 'var(--gray-50)',
            borderRadius: 'var(--radius-md)',
            textAlign: 'center'
          }}>
            <p style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              lineHeight: '1.4'
            }}>
              Medical device for rehabilitation use. Consult your healthcare provider.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;