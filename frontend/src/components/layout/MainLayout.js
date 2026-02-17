import React from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

const MainLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const navigationTabs = [
    {
      id: 'home',
      label: 'Home',
      path: '/dashboard',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9,22 9,12 15,12 15,22"/>
        </svg>
      )
    },
    {
      id: 'session',
      label: 'Session',
      path: '/session',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12,6 12,12 16,14"/>
        </svg>
      )
    },
    {
      id: 'analytics',
      label: 'Analytics',
      path: '/analytics',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
        </svg>
      )
    },
    {
      id: 'support',
      label: 'Support',
      path: '/support',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 12l2 2 4-4"/>
          <path d="M21 12c.552 0 1-.448 1-1V8a2 2 0 0 0-2-2h-1l-1-2h-3l-1 2H9L8 4H5a2 2 0 0 0-2 2v3c0 .552.448 1 1 1"/>
          <circle cx="9" cy="16" r="5"/>
        </svg>
      )
    },
    {
      id: 'settings',
      label: 'Settings',
      path: '/settings',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m17-4a4 4 0 0 1-8 0 4 4 0 0 1 8 0zM7 21a4 4 0 0 1-8 0 4 4 0 0 1 8 0z"/>
        </svg>
      )
    }
  ];

  const isActiveTab = (path) => {
    return location.pathname === path;
  };

  const handleTabClick = (path) => {
    navigate(path);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      backgroundColor: 'var(--gray-50)'
    }}>
      {/* Header */}
      <header style={{
        backgroundColor: 'white',
        borderBottom: '1px solid var(--gray-200)',
        padding: 'var(--spacing-4)',
        position: 'sticky',
        top: 0,
        zIndex: 10,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h1 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--primary-blue)',
            margin: 0
          }}>
            Vertex
          </h1>
          
          <button
            onClick={() => {
              // Clear demo data and redirect to landing
              localStorage.removeItem('currentUserEmail');
              localStorage.removeItem('onboardingComplete');
              localStorage.removeItem('userEmail');
              navigate('/auth/');
            }}
            style={{
              backgroundColor: 'transparent',
              border: '1px solid var(--gray-300)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-2) var(--spacing-3)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              cursor: 'pointer',
              transition: 'var(--transition-fast)'
            }}
            onMouseOver={(e) => {
              e.target.style.backgroundColor = 'var(--gray-100)';
            }}
            onMouseOut={(e) => {
              e.target.style.backgroundColor = 'transparent';
            }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{
        flex: 1,
        paddingBottom: '80px', // Space for bottom navigation
        overflow: 'auto'
      }}>
        <Outlet />
      </main>

      {/* Bottom Navigation */}
      <nav style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: 'white',
        borderTop: '1px solid var(--gray-200)',
        padding: 'var(--spacing-2) 0',
        boxShadow: '0 -2px 10px rgba(0, 0, 0, 0.1)',
        zIndex: 20
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center',
          maxWidth: '600px',
          margin: '0 auto'
        }}>
          {navigationTabs.map((tab) => {
            const isActive = isActiveTab(tab.path);
            
            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab.path)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  padding: 'var(--spacing-2)',
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: isActive ? 'var(--primary-blue)' : 'var(--gray-500)',
                  transition: 'var(--transition-fast)',
                  minWidth: '60px',
                  minHeight: '60px',
                  borderRadius: 'var(--border-radius-md)'
                }}
                onMouseOver={(e) => {
                  if (!isActive) {
                    e.target.style.backgroundColor = 'var(--gray-100)';
                  }
                }}
                onMouseOut={(e) => {
                  if (!isActive) {
                    e.target.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <div style={{
                  marginBottom: 'var(--spacing-1)',
                  transform: isActive ? 'scale(1.1)' : 'scale(1)',
                  transition: 'var(--transition-fast)'
                }}>
                  {tab.icon}
                </div>
                <span style={{
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: isActive ? '600' : '400',
                  textAlign: 'center'
                }}>
                  {tab.label}
                </span>
                
                {/* Active indicator */}
                {isActive && (
                  <div style={{
                    position: 'absolute',
                    bottom: '2px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: '4px',
                    height: '4px',
                    backgroundColor: 'var(--primary-blue)',
                    borderRadius: '50%'
                  }} />
                )}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
};

export default MainLayout;