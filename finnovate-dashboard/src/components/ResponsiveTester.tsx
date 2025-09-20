import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Chip, Alert } from '@mui/material';
import { Smartphone, Tablet, Computer } from '@mui/icons-material';

const ResponsiveTester: React.FC = () => {
  const [screenSize, setScreenSize] = useState({ width: 0, height: 0 });
  const [deviceType, setDeviceType] = useState('');

  useEffect(() => {
    const updateScreenSize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      setScreenSize({ width, height });

      if (width < 600) {
        setDeviceType('Mobile');
      } else if (width < 960) {
        setDeviceType('Tablet');
      } else {
        setDeviceType('Desktop');
      }
    };

    updateScreenSize();
    window.addEventListener('resize', updateScreenSize);
    return () => window.removeEventListener('resize', updateScreenSize);
  }, []);

  const getDeviceIcon = () => {
    switch (deviceType) {
      case 'Mobile': return <Smartphone />;
      case 'Tablet': return <Tablet />;
      default: return <Computer />;
    }
  };

  const getDeviceColor = () => {
    switch (deviceType) {
      case 'Mobile': return 'error';
      case 'Tablet': return 'warning';
      default: return 'success';
    }
  };

  const breakpoints = [
    { name: 'xs', min: 0, max: 599, description: 'Extra small devices' },
    { name: 'sm', min: 600, max: 959, description: 'Small devices' },
    { name: 'md', min: 960, max: 1279, description: 'Medium devices' },
    { name: 'lg', min: 1280, max: 1919, description: 'Large devices' },
    { name: 'xl', min: 1920, max: Infinity, description: 'Extra large devices' },
  ];

  const currentBreakpoint = breakpoints.find(bp => 
    screenSize.width >= bp.min && screenSize.width <= bp.max
  );

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Responsive Design Tester
      </Typography>
      
      <Box display="flex" alignItems="center" gap={2} mb={2}>
        {getDeviceIcon()}
        <Chip 
          label={deviceType} 
          color={getDeviceColor() as any} 
        />
        <Typography variant="body2">
          {screenSize.width} × {screenSize.height}
        </Typography>
      </Box>

      {currentBreakpoint && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Current breakpoint: <strong>{currentBreakpoint.name}</strong> - {currentBreakpoint.description}
        </Alert>
      )}

      <Typography variant="subtitle2" gutterBottom>
        MUI Breakpoints:
      </Typography>
      
      {breakpoints.map((bp) => (
        <Box 
          key={bp.name}
          display="flex" 
          justifyContent="space-between" 
          alignItems="center"
          py={0.5}
          sx={{
            bgcolor: currentBreakpoint?.name === bp.name ? 'primary.50' : 'transparent',
            borderRadius: 1,
            px: 1
          }}
        >
          <Typography variant="body2">
            <strong>{bp.name}:</strong> {bp.description}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {bp.min}px - {bp.max === Infinity ? '∞' : `${bp.max}px`}
          </Typography>
        </Box>
      ))}

      <Box mt={2}>
        <Typography variant="caption" color="textSecondary">
          Resize your browser window to test different breakpoints
        </Typography>
      </Box>
    </Paper>
  );
};

export default ResponsiveTester;