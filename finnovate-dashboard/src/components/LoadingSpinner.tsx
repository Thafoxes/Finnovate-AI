import React from 'react';
import { Box, CircularProgress, Typography, Skeleton } from '@mui/material';

interface LoadingSpinnerProps {
  size?: number;
  message?: string;
  variant?: 'spinner' | 'skeleton';
  rows?: number;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 40, 
  message = 'Loading...', 
  variant = 'spinner',
  rows = 5 
}) => {
  if (variant === 'skeleton') {
    return (
      <Box>
        {Array.from({ length: rows }).map((_, index) => (
          <Skeleton key={index} variant="rectangular" height={60} sx={{ mb: 1 }} />
        ))}
      </Box>
    );
  }

  return (
    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" py={4}>
      <CircularProgress size={size} />
      {message && (
        <Typography variant="body2" color="textSecondary" mt={2}>
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default LoadingSpinner;