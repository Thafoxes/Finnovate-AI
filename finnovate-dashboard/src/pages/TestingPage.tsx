import React from 'react';
import { Box, Typography, Grid } from '@mui/material';
import ApiTester from '../components/ApiTester';
import ResponsiveTester from '../components/ResponsiveTester';

const TestingPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Integration & Testing
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <ApiTester />
        </Grid>
        <Grid item xs={12} lg={4}>
          <ResponsiveTester />
        </Grid>
      </Grid>
    </Box>
  );
};

export default TestingPage;