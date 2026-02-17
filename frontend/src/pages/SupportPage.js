import React from 'react';

const SupportPage = () => {
  const handleEmergencyCall = () => {
    window.location.href = 'tel:911';
  };

  const handleContactProvider = () => {
    // TODO: Implement healthcare provider contact
    alert('Healthcare provider contact feature coming soon');
  };

  const handleContactSupport = () => {
    // TODO: Implement support team contact
    alert('Support team contact feature coming soon');
  };

  const faqItems = [
    {
      question: 'How do I calibrate my device?',
      answer: 'Go to Settings > Device Calibration and follow the step-by-step instructions. Make sure you are in a comfortable, upright position when starting calibration.'
    },
    {
      question: 'What should I do if the device is not connecting?',
      answer: 'Check that your device is powered on and within range. Try restarting both the device and the app. If issues persist, contact support.'
    },
    {
      question: 'How often should I use the device?',
      answer: 'Follow your healthcare provider\'s recommendations. Typically, 2-3 sessions per day of 15-30 minutes each is recommended for optimal results.'
    },
    {
      question: 'Is the haptic feedback safe?',
      answer: 'Yes, the vibration feedback is designed to be gentle and safe. If you experience any discomfort, you can adjust the intensity in Settings or contact your healthcare provider.'
    }
  ];

  return (
    <div style={{
      padding: 'var(--spacing-4)',
      maxWidth: '1200px',
      margin: '0 auto',
      minHeight: 'calc(100vh - 160px)' // Account for header and bottom nav
    }}>
      {/* Page Header */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--gray-100)'
      }}>
        <h1 style={{
          fontSize: 'var(--font-size-2xl)',
          fontWeight: '700',
          color: 'var(--gray-900)',
          marginBottom: 'var(--spacing-2)',
          letterSpacing: '-0.025em',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-3)'
        }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
            <path d="M9 12l2 2 4-4"/>
            <path d="M21 12c.552 0 1-.448 1-1V8a2 2 0 0 0-2-2h-1l-1-2h-4l-1 2h-1a2 2 0 0 0-2 2v3c0 .552.448 1 1 1"/>
            <circle cx="9" cy="16" r="5"/>
          </svg>
          Support & Help
        </h1>
        <p style={{
          fontSize: 'var(--font-size-lg)',
          color: 'var(--gray-600)',
          lineHeight: '1.6',
          margin: 0
        }}>
          Get assistance with your Vertex rehabilitation device and access emergency contacts.
        </p>
      </div>

      {/* Main Content Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)'
      }}>
        {/* Emergency Contact */}
        <div style={{
          backgroundColor: '#fef2f2',
          border: '2px solid #fecaca',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-3)',
            marginBottom: 'var(--spacing-4)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
            <h2 style={{
              fontSize: 'var(--font-size-xl)',
              fontWeight: '700',
              color: '#dc2626',
              margin: 0
            }}>
              Emergency Contact
            </h2>
          </div>
          <p style={{
            fontSize: 'var(--font-size-base)',
            color: '#7f1d1d',
            marginBottom: 'var(--spacing-4)',
            lineHeight: '1.6',
            fontWeight: '500'
          }}>
            If you are experiencing a medical emergency, call 911 immediately.
          </p>
          <button
            onClick={handleEmergencyCall}
            style={{
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-4) var(--spacing-6)',
              fontSize: 'var(--font-size-lg)',
              fontWeight: '700',
              cursor: 'pointer',
              width: '100%',
              minHeight: '56px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 'var(--spacing-2)',
              transition: 'var(--transition-fast)'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#b91c1c'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#dc2626'}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
            Call 911
          </button>
        </div>

        {/* Quick Contacts */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-xl)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            Quick Contacts
          </h3>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-4)'
          }}>
            <button
              onClick={handleContactProvider}
              style={{
                width: '100%',
                padding: 'var(--spacing-4)',
                backgroundColor: 'var(--gray-50)',
                border: '2px solid var(--gray-200)',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                transition: 'var(--transition-fast)',
                textAlign: 'left',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-3)',
                minHeight: '72px'
              }}
              onMouseOver={(e) => {
                e.target.style.backgroundColor = 'var(--primary-blue-50)';
                e.target.style.borderColor = 'var(--primary-blue-200)';
              }}
              onMouseOut={(e) => {
                e.target.style.backgroundColor = 'var(--gray-50)';
                e.target.style.borderColor = 'var(--gray-200)';
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
              <div>
                <div style={{ 
                  fontWeight: '600', 
                  fontSize: 'var(--font-size-base)',
                  color: 'var(--gray-900)',
                  marginBottom: 'var(--spacing-1)'
                }}>
                  Healthcare Provider
                </div>
                <div style={{ 
                  fontSize: 'var(--font-size-sm)', 
                  color: 'var(--gray-600)',
                  lineHeight: '1.4'
                }}>
                  Contact your assigned therapist or doctor
                </div>
              </div>
            </button>

            <button
              onClick={handleContactSupport}
              style={{
                width: '100%',
                padding: 'var(--spacing-4)',
                backgroundColor: 'var(--gray-50)',
                border: '2px solid var(--gray-200)',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                transition: 'var(--transition-fast)',
                textAlign: 'left',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-3)',
                minHeight: '72px'
              }}
              onMouseOver={(e) => {
                e.target.style.backgroundColor = 'var(--primary-blue-50)';
                e.target.style.borderColor = 'var(--primary-blue-200)';
              }}
              onMouseOut={(e) => {
                e.target.style.backgroundColor = 'var(--gray-50)';
                e.target.style.borderColor = 'var(--gray-200)';
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
                <path d="M14.828 14.828a4 4 0 0 1-5.656 0"/>
                <path d="M9 9a3 3 0 1 1 6 0c0 2-3 3-3 3"/>
                <path d="M12 17h.01"/>
              </svg>
              <div>
                <div style={{ 
                  fontWeight: '600', 
                  fontSize: 'var(--font-size-base)',
                  color: 'var(--gray-900)',
                  marginBottom: 'var(--spacing-1)'
                }}>
                  Technical Support
                </div>
                <div style={{ 
                  fontSize: 'var(--font-size-sm)', 
                  color: 'var(--gray-600)',
                  lineHeight: '1.4'
                }}>
                  Get help with device issues or app problems
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Section Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: 'var(--spacing-6)'
      }}>
        {/* FAQ Section */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-xl)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <path d="M12 17h.01"/>
            </svg>
            Frequently Asked Questions
          </h3>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-4)'
          }}>
            {faqItems.map((item, index) => (
              <div key={index} style={{
                padding: 'var(--spacing-4)',
                backgroundColor: 'var(--gray-50)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--gray-200)'
              }}>
                <h4 style={{
                  fontSize: 'var(--font-size-base)',
                  fontWeight: '600',
                  color: 'var(--gray-900)',
                  marginBottom: 'var(--spacing-2)'
                }}>
                  {item.question}
                </h4>
                <p style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--gray-700)',
                  lineHeight: '1.6',
                  margin: 0
                }}>
                  {item.answer}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Additional Resources */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-xl)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            Additional Resources
          </h3>

          <div style={{
            padding: 'var(--spacing-5)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--primary-blue-200)',
            marginBottom: 'var(--spacing-4)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-2)',
              marginBottom: 'var(--spacing-2)'
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              <h4 style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: '600',
                color: 'var(--primary-blue)',
                margin: 0
              }}>
                Coming Soon
              </h4>
            </div>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--primary-blue)',
              margin: 0,
              lineHeight: '1.6',
              opacity: 0.9
            }}>
              Educational materials, exercise guides, and rehabilitation resources will be available here. 
              Check back regularly for updates and new content from your healthcare team.
            </p>
          </div>

          {/* Resource Categories Preview */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 'var(--spacing-3)'
          }}>
            <div style={{
              padding: 'var(--spacing-3)',
              backgroundColor: 'var(--gray-50)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--gray-200)',
              textAlign: 'center'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2" style={{ marginBottom: 'var(--spacing-2)' }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
              </svg>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: '500',
                color: 'var(--gray-600)'
              }}>
                Exercise Guides
              </div>
            </div>

            <div style={{
              padding: 'var(--spacing-3)',
              backgroundColor: 'var(--gray-50)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--gray-200)',
              textAlign: 'center'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2" style={{ marginBottom: 'var(--spacing-2)' }}>
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: '500',
                color: 'var(--gray-600)'
              }}>
                Device Setup
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupportPage;