// Data Cleanup System for Browser Security
// Requirement 9.7: Clear sensitive data from browser memory on session end

/**
 * Secure data cleanup utilities for medical device compliance.
 * Ensures sensitive patient data is properly cleared from browser memory
 * when sessions end or components unmount.
 */

class DataCleanupManager {
  constructor() {
    this.sensitiveDataKeys = new Set();
    this.cleanupCallbacks = new Map();
    this.isCleanupActive = false;
    
    // Register cleanup on page unload
    this.registerUnloadCleanup();
    
    // Register cleanup on visibility change (tab switching)
    this.registerVisibilityCleanup();
  }
  
  /**
   * Register a data key as containing sensitive information.
   * @param {string} key - The data key to track
   * @param {Function} cleanupCallback - Optional custom cleanup function
   */
  registerSensitiveData(key, cleanupCallback = null) {
    this.sensitiveDataKeys.add(key);
    
    if (cleanupCallback) {
      this.cleanupCallbacks.set(key, cleanupCallback);
    }
    
    console.debug(`Registered sensitive data key: ${key}`);
  }
  
  /**
   * Unregister a data key from sensitive tracking.
   * @param {string} key - The data key to stop tracking
   */
  unregisterSensitiveData(key) {
    this.sensitiveDataKeys.delete(key);
    this.cleanupCallbacks.delete(key);
    
    console.debug(`Unregistered sensitive data key: ${key}`);
  }
  
  /**
   * Perform immediate cleanup of all registered sensitive data.
   */
  performCleanup() {
    if (this.isCleanupActive) {
      return; // Prevent recursive cleanup
    }
    
    this.isCleanupActive = true;
    
    try {
      console.info('Starting sensitive data cleanup...');
      
      // Clear localStorage
      this.clearLocalStorage();
      
      // Clear sessionStorage
      this.clearSessionStorage();
      
      // Clear cookies
      this.clearCookies();
      
      // Clear IndexedDB
      this.clearIndexedDB();
      
      // Execute custom cleanup callbacks
      this.executeCleanupCallbacks();
      
      // Clear browser cache (if possible)
      this.clearBrowserCache();
      
      // Force garbage collection (if available)
      this.forceGarbageCollection();
      
      console.info('Sensitive data cleanup completed');
      
    } catch (error) {
      console.error('Error during data cleanup:', error);
    } finally {
      this.isCleanupActive = false;
    }
  }
  
  /**
   * Clear sensitive data from localStorage.
   */
  clearLocalStorage() {
    try {
      const keysToRemove = [];
      
      // Find keys that contain sensitive data
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (this.isSensitiveKey(key)) {
          keysToRemove.push(key);
        }
      }
      
      // Remove sensitive keys
      keysToRemove.forEach(key => {
        localStorage.removeItem(key);
        console.debug(`Cleared localStorage key: ${key}`);
      });
      
      // Clear known sensitive patterns
      this.clearStorageByPattern(localStorage, [
        'patient_',
        'user_',
        'auth_',
        'session_',
        'token_',
        'supabase.',
        'vertex_'
      ]);
      
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  }
  
  /**
   * Clear sensitive data from sessionStorage.
   */
  clearSessionStorage() {
    try {
      const keysToRemove = [];
      
      // Find keys that contain sensitive data
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (this.isSensitiveKey(key)) {
          keysToRemove.push(key);
        }
      }
      
      // Remove sensitive keys
      keysToRemove.forEach(key => {
        sessionStorage.removeItem(key);
        console.debug(`Cleared sessionStorage key: ${key}`);
      });
      
      // Clear known sensitive patterns
      this.clearStorageByPattern(sessionStorage, [
        'patient_',
        'user_',
        'auth_',
        'session_',
        'token_',
        'supabase.',
        'vertex_'
      ]);
      
    } catch (error) {
      console.error('Error clearing sessionStorage:', error);
    }
  }
  
  /**
   * Clear sensitive cookies.
   */
  clearCookies() {
    try {
      const cookies = document.cookie.split(';');
      
      cookies.forEach(cookie => {
        const [name] = cookie.split('=');
        const cookieName = name.trim();
        
        if (this.isSensitiveKey(cookieName)) {
          // Clear cookie by setting expiration to past date
          document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${window.location.hostname}`;
          document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
          console.debug(`Cleared cookie: ${cookieName}`);
        }
      });
      
    } catch (error) {
      console.error('Error clearing cookies:', error);
    }
  }
  
  /**
   * Clear sensitive data from IndexedDB.
   */
  async clearIndexedDB() {
    try {
      if (!window.indexedDB) {
        return;
      }
      
      // Get list of databases
      const databases = await indexedDB.databases();
      
      for (const db of databases) {
        if (this.isSensitiveKey(db.name)) {
          const deleteRequest = indexedDB.deleteDatabase(db.name);
          
          await new Promise((resolve, reject) => {
            deleteRequest.onsuccess = () => {
              console.debug(`Cleared IndexedDB: ${db.name}`);
              resolve();
            };
            deleteRequest.onerror = () => reject(deleteRequest.error);
          });
        }
      }
      
    } catch (error) {
      console.error('Error clearing IndexedDB:', error);
    }
  }
  
  /**
   * Execute custom cleanup callbacks.
   */
  executeCleanupCallbacks() {
    try {
      this.cleanupCallbacks.forEach((callback, key) => {
        try {
          callback();
          console.debug(`Executed cleanup callback for: ${key}`);
        } catch (error) {
          console.error(`Error in cleanup callback for ${key}:`, error);
        }
      });
    } catch (error) {
      console.error('Error executing cleanup callbacks:', error);
    }
  }
  
  /**
   * Clear browser cache (limited by browser security).
   */
  clearBrowserCache() {
    try {
      // Clear service worker cache if available
      if ('serviceWorker' in navigator && 'caches' in window) {
        caches.keys().then(cacheNames => {
          cacheNames.forEach(cacheName => {
            if (this.isSensitiveKey(cacheName)) {
              caches.delete(cacheName);
              console.debug(`Cleared cache: ${cacheName}`);
            }
          });
        });
      }
    } catch (error) {
      console.error('Error clearing browser cache:', error);
    }
  }
  
  /**
   * Force garbage collection if available.
   */
  forceGarbageCollection() {
    try {
      // Force garbage collection in development (Chrome DevTools)
      if (window.gc && typeof window.gc === 'function') {
        window.gc();
        console.debug('Forced garbage collection');
      }
    } catch (error) {
      console.error('Error forcing garbage collection:', error);
    }
  }
  
  /**
   * Check if a key contains sensitive data.
   * @param {string} key - The key to check
   * @returns {boolean} - True if the key is sensitive
   */
  isSensitiveKey(key) {
    if (!key) return false;
    
    // Check registered sensitive keys
    if (this.sensitiveDataKeys.has(key)) {
      return true;
    }
    
    // Check for sensitive patterns
    const sensitivePatterns = [
      /patient/i,
      /user/i,
      /auth/i,
      /token/i,
      /session/i,
      /password/i,
      /email/i,
      /phone/i,
      /medical/i,
      /clinical/i,
      /supabase/i,
      /vertex/i,
      /sensor/i,
      /device/i
    ];
    
    return sensitivePatterns.some(pattern => pattern.test(key));
  }
  
  /**
   * Clear storage items matching specific patterns.
   * @param {Storage} storage - localStorage or sessionStorage
   * @param {string[]} patterns - Array of string patterns to match
   */
  clearStorageByPattern(storage, patterns) {
    try {
      const keysToRemove = [];
      
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        
        if (patterns.some(pattern => key && key.includes(pattern))) {
          keysToRemove.push(key);
        }
      }
      
      keysToRemove.forEach(key => {
        storage.removeItem(key);
        console.debug(`Cleared storage key by pattern: ${key}`);
      });
      
    } catch (error) {
      console.error('Error clearing storage by pattern:', error);
    }
  }
  
  /**
   * Register cleanup on page unload.
   */
  registerUnloadCleanup() {
    // Handle page unload
    window.addEventListener('beforeunload', () => {
      this.performCleanup();
    });
    
    // Handle page hide (mobile browsers)
    window.addEventListener('pagehide', () => {
      this.performCleanup();
    });
    
    // Handle browser close
    window.addEventListener('unload', () => {
      this.performCleanup();
    });
  }
  
  /**
   * Register cleanup on visibility change.
   */
  registerVisibilityCleanup() {
    document.addEventListener('visibilitychange', () => {
      // Clean up when tab becomes hidden (user switches tabs)
      if (document.hidden) {
        // Delay cleanup to avoid interfering with normal tab switching
        setTimeout(() => {
          if (document.hidden) {
            this.performCleanup();
          }
        }, 30000); // 30 seconds delay
      }
    });
  }
  
  /**
   * Schedule automatic cleanup after a specified time.
   * @param {number} minutes - Minutes until cleanup
   */
  scheduleCleanup(minutes = 30) {
    setTimeout(() => {
      this.performCleanup();
    }, minutes * 60 * 1000);
    
    console.info(`Scheduled automatic cleanup in ${minutes} minutes`);
  }
}

// Create global cleanup manager instance
const dataCleanupManager = new DataCleanupManager();

/**
 * React hook for automatic data cleanup on component unmount.
 * @param {string[]} sensitiveKeys - Array of sensitive data keys to track
 * @param {Function} customCleanup - Optional custom cleanup function
 */
export const useDataCleanup = (sensitiveKeys = [], customCleanup = null) => {
  const { useEffect } = require('react');
  
  useEffect(() => {
    // Register sensitive keys
    sensitiveKeys.forEach(key => {
      dataCleanupManager.registerSensitiveData(key);
    });
    
    // Register custom cleanup
    if (customCleanup) {
      dataCleanupManager.registerSensitiveData('custom', customCleanup);
    }
    
    // Cleanup on unmount
    return () => {
      sensitiveKeys.forEach(key => {
        dataCleanupManager.unregisterSensitiveData(key);
      });
      
      if (customCleanup) {
        dataCleanupManager.unregisterSensitiveData('custom');
      }
    };
  }, [sensitiveKeys, customCleanup]);
  
  return {
    performCleanup: () => dataCleanupManager.performCleanup(),
    registerSensitiveData: (key, callback) => dataCleanupManager.registerSensitiveData(key, callback),
    scheduleCleanup: (minutes) => dataCleanupManager.scheduleCleanup(minutes)
  };
};

/**
 * Secure session management with automatic cleanup.
 */
export class SecureSessionManager {
  constructor() {
    this.sessionTimeout = 30 * 60 * 1000; // 30 minutes
    this.warningTimeout = 25 * 60 * 1000; // 25 minutes (5 min warning)
    this.timeoutId = null;
    this.warningId = null;
    
    this.startSessionTimer();
  }
  
  startSessionTimer() {
    this.clearTimers();
    
    // Set warning timer
    this.warningId = setTimeout(() => {
      this.showSessionWarning();
    }, this.warningTimeout);
    
    // Set session timeout
    this.timeoutId = setTimeout(() => {
      this.endSession();
    }, this.sessionTimeout);
  }
  
  resetSessionTimer() {
    this.startSessionTimer();
  }
  
  clearTimers() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    
    if (this.warningId) {
      clearTimeout(this.warningId);
      this.warningId = null;
    }
  }
  
  showSessionWarning() {
    console.warn('Session will expire in 5 minutes');
    
    // Dispatch custom event for UI components to handle
    window.dispatchEvent(new CustomEvent('sessionWarning', {
      detail: { remainingTime: 5 * 60 * 1000 }
    }));
  }
  
  endSession() {
    console.info('Session expired - performing cleanup');
    
    // Perform data cleanup
    dataCleanupManager.performCleanup();
    
    // Dispatch session end event
    window.dispatchEvent(new CustomEvent('sessionExpired'));
    
    // Redirect to login (if needed)
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }
  
  extendSession() {
    this.resetSessionTimer();
    console.info('Session extended');
  }
}

// Export utilities
export { dataCleanupManager, DataCleanupManager };

// Auto-register common sensitive data patterns
dataCleanupManager.registerSensitiveData('supabase.auth.token');
dataCleanupManager.registerSensitiveData('vertex_patient_data');
dataCleanupManager.registerSensitiveData('vertex_session_data');
dataCleanupManager.registerSensitiveData('vertex_device_data');

// Schedule automatic cleanup every 4 hours
dataCleanupManager.scheduleCleanup(240);

export default dataCleanupManager;