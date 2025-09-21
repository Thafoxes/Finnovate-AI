// Console cleaner for demo mode
// This suppresses CORS and network errors during demonstrations

const originalError = console.error;
const originalWarn = console.warn;

// List of error patterns to suppress during demo
const suppressPatterns = [
  'CORS',
  'Failed to fetch',
  'NetworkError',
  'TypeError: Failed to fetch',
  'Access to fetch at',
  'has been blocked by CORS policy',
  'ERR_FAILED',
  'net::ERR_FAILED'
];

// Override console.error to filter demo-related errors
console.error = (...args) => {
  const message = args.join(' ');
  
  // Check if this is a suppressed error pattern
  const shouldSuppress = suppressPatterns.some(pattern => 
    message.toLowerCase().includes(pattern.toLowerCase())
  );
  
  // Only show non-suppressed errors in demo mode
  if (!shouldSuppress || process.env.REACT_APP_DEBUG_MODE === 'true') {
    originalError.apply(console, args);
  }
};

// Override console.warn for cleaner demo experience
console.warn = (...args) => {
  const message = args.join(' ');
  
  // Suppress CORS-related warnings
  const shouldSuppress = suppressPatterns.some(pattern => 
    message.toLowerCase().includes(pattern.toLowerCase())
  );
  
  if (!shouldSuppress || process.env.REACT_APP_DEBUG_MODE === 'true') {
    originalWarn.apply(console, args);
  }
};

export {};