import React from 'react';
import { Box, Typography, Card, CardContent, Grid } from '@mui/material';
import { People, TrendingUp, Warning } from '@mui/icons-material';
import { useCustomers } from '../hooks/useCustomers';
import AmountDisplay from './AmountDisplay';

const CustomerStats: React.FC = () => {
  const { data: customers = [] } = useCustomers();

  const stats = {
    totalCustomers: customers.length,
    activeCustomers: customers.filter(c => c.outstanding_amount > 0).length,
    highRiskCustomers: customers.filter(c => 
      c.total_amount > 0 && (c.outstanding_amount / c.total_amount) > 0.7
    ).length,
    avgOutstanding: customers.length > 0 ? 
      customers.reduce((sum, c) => sum + c.outstanding_amount, 0) / customers.length : 0,
  };

  const StatCard = ({ title, value, icon, color = 'primary' }: any) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h5">
              {typeof value === 'number' && title.includes('Outstanding') ? 
                <AmountDisplay amount={value} variant="h6" /> : value
              }
            </Typography>
          </Box>
          <Box color={`${color}.main`}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Customer Overview
      </Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Customers"
            value={stats.totalCustomers}
            icon={<People fontSize="large" />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Customers"
            value={stats.activeCustomers}
            icon={<TrendingUp fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="High Risk Customers"
            value={stats.highRiskCustomers}
            icon={<Warning fontSize="large" />}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Outstanding"
            value={stats.avgOutstanding}
            icon={<TrendingUp fontSize="large" />}
            color="warning"
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default CustomerStats;