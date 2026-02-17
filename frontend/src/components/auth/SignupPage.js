import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const SignupPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    age: '',
    password: '',
    confirmPassword: '',
    notificationsEnabled: true,
    agreeToTerms: false
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
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
    
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    }
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (formData.age && (formData.age < 18 || formData.age > 120)) {
      newErrors.age = 'Please enter a valid age (18-120)';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = 'You must agree to the terms of service';
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
    
    // Simulate signup for now - remove Supabase temporarily
    setTimeout(() => {
      // Store the new user info
      localStorage.setItem('currentUserEmail', formData.email);
      localStorage.removeItem('onboardingComplete'); // New user hasn't completed onboarding
      
      setErrors({ success: 'Account created successfully! Redirecting to getting started...' });
      setTimeout(() => {
        navigate('/auth/onboarding');
      }, 2000);
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
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-6)' }}>
            <h1 style={{
              fontSize: 'var(--font-size-xl)',
              fontWeight: '600',
              color: 'var(--gray-900)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Create Account
            </h1>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)'
            }}>
              Start your rehabilitation journey
            </p>
          </div>

          {/* Signup Form */}
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

            {errors.success && (
              <div style={{
                color: 'var(--success-green)',
                fontSize: 'var(--font-size-sm)',
                marginBottom: 'var(--spacing-4)',
                padding: 'var(--spacing-3)',
                backgroundColor: '#F0FDF4',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #BBF7D0'
              }}>
                {errors.success}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="fullName" className="form-label">
                Full Name
              </label>
              <input
                type="text"
                id="fullName"
                name="fullName"
                className="form-input"
                placeholder="John Smith"
                value={formData.fullName}
                onChange={handleInputChange}
                disabled={loading}
                style={{
                  borderColor: errors.fullName ? 'var(--danger-red)' : undefined
                }}
              />
              {errors.fullName && (
                <div style={{
                  color: 'var(--danger-red)',
                  fontSize: 'var(--font-size-sm)',
                  marginTop: 'var(--spacing-1)'
                }}>
                  {errors.fullName}
                </div>
              )}
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
              <label htmlFor="phone" className="form-label">
                Phone Number
              </label>
              <input
                type="tel"
                id="phone"
                name="phone"
                className="form-input"
                placeholder="(555) 123-4567"
                value={formData.phone}
                onChange={handleInputChange}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="age" className="form-label">
                Age
              </label>
              <input
                type="number"
                id="age"
                name="age"
                className="form-input"
                placeholder="65"
                min="18"
                max="120"
                value={formData.age}
                onChange={handleInputChange}
                disabled={loading}
                style={{
                  borderColor: errors.age ? 'var(--danger-red)' : undefined
                }}
              />
              {errors.age && (
                <div style={{
                  color: 'var(--danger-red)',
                  fontSize: 'var(--font-size-sm)',
                  marginTop: 'var(--spacing-1)'
                }}>
                  {errors.age}
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
                placeholder="Create a secure password"
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

            <div className="form-group">
              <label htmlFor="confirmPassword" className="form-label">
                Confirm Password
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                className="form-input"
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                disabled={loading}
                style={{
                  borderColor: errors.confirmPassword ? 'var(--danger-red)' : undefined
                }}
              />
              {errors.confirmPassword && (
                <div style={{
                  color: 'var(--danger-red)',
                  fontSize: 'var(--font-size-sm)',
                  marginTop: 'var(--spacing-1)'
                }}>
                  {errors.confirmPassword}
                </div>
              )}
            </div>

            {/* Notifications Toggle */}
            <div className="form-group">
              <div style={{
                display: 'flex',
                alignItems: 'center',
                padding: 'var(--spacing-3)',
                backgroundColor: 'var(--primary-blue-50)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--primary-blue-200)'
              }}>
                <div style={{
                  width: '24px',
                  height: '24px',
                  backgroundColor: 'var(--primary-blue)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: 'var(--spacing-3)',
                  flexShrink: 0
                }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: 'var(--font-size-sm)',
                    fontWeight: '500',
                    color: 'var(--gray-900)',
                    marginBottom: 'var(--spacing-1)'
                  }}>
                    Allow Notifications
                  </div>
                  <div style={{
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--gray-600)'
                  }}>
                    Receive reminders and progress updates
                  </div>
                </div>
                <label style={{
                  position: 'relative',
                  display: 'inline-block',
                  width: '44px',
                  height: '24px',
                  cursor: 'pointer'
                }}>
                  <input
                    type="checkbox"
                    name="notificationsEnabled"
                    checked={formData.notificationsEnabled}
                    onChange={handleInputChange}
                    disabled={loading}
                    style={{ display: 'none' }}
                  />
                  <span style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: formData.notificationsEnabled ? 'var(--primary-blue)' : 'var(--gray-300)',
                    borderRadius: '12px',
                    transition: 'var(--transition-fast)',
                    cursor: 'pointer'
                  }}>
                    <span style={{
                      position: 'absolute',
                      content: '',
                      height: '18px',
                      width: '18px',
                      left: formData.notificationsEnabled ? '23px' : '3px',
                      bottom: '3px',
                      backgroundColor: 'white',
                      borderRadius: '50%',
                      transition: 'var(--transition-fast)'
                    }} />
                  </span>
                </label>
              </div>
            </div>

            {/* Terms Agreement */}
            <div className="form-group">
              <label style={{
                display: 'flex',
                alignItems: 'flex-start',
                cursor: 'pointer',
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-700)'
              }}>
                <input
                  type="checkbox"
                  name="agreeToTerms"
                  checked={formData.agreeToTerms}
                  onChange={handleInputChange}
                  disabled={loading}
                  style={{
                    marginRight: 'var(--spacing-2)',
                    marginTop: '2px',
                    accentColor: 'var(--primary-blue)'
                  }}
                />
                <span>
                  By creating an account, you agree to our Terms of Service and Privacy Policy. 
                  Your health data will be shared with your healthcare provider with your explicit consent.
                </span>
              </label>
              {errors.agreeToTerms && (
                <div style={{
                  color: 'var(--danger-red)',
                  fontSize: 'var(--font-size-sm)',
                  marginTop: 'var(--spacing-1)'
                }}>
                  {errors.agreeToTerms}
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
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          {/* Switch to Login */}
          <div style={{ textAlign: 'center' }}>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Already have an account?
            </p>
            <Link
              to="/auth/login"
              className="btn btn-secondary"
              style={{ 
                width: '100%',
                textDecoration: 'none',
                display: 'inline-block',
                textAlign: 'center',
                marginBottom: 'var(--spacing-3)'
              }}
            >
              Log In
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
        </div>
      </div>
    </div>
  );
};

export default SignupPage;