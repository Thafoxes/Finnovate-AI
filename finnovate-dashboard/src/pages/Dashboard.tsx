import React from 'react';
import { Box, Grid, Paper, Typography, Card, CardContent, Button } from '@mui/material';
import { Receipt, AttachMoney, Schedule, TrendingUp } from '@mui/icons-material';
import { useInvoices } from '../hooks/useInvoices';
import { useRawDataCalculations } from '../hooks/useRawDataCalculations';
import AmountDisplay from '../components/AmountDisplay';
import CustomerStats from '../components/CustomerStats';
import LoadingSpinner from '../components/LoadingSpinner';
import { CardSkeleton, ChartSkeleton } from '../components/LoadingSkeleton';
import { OptimizedCashFlowChart, OptimizedOverdueChart, OptimizedCustomerRiskChart } from '../components/OptimizedCharts';

const Dashboard: React.FC = () => {
  const { data: invoices = [], isLoading, error } = useInvoices();
  const { basicStats: stats, cashFlowData, customerSegments, overdueAnalysis } = useRawDataCalculations(Array.isArray(invoices) ? invoices : []);
  
  // Debug logging
  console.log('Dashboard - invoices:', invoices);
  console.log('Dashboard - isLoading:', isLoading);
  console.log('Dashboard - error:', error);
  console.log('Dashboard - stats:', stats);
  


  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>Dashboard</Typography>
        <Grid container spacing={3} mb={4}>
          {[...Array(4)].map((_, i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <CardSkeleton />
            </Grid>
          ))}
        </Grid>
        <Grid container spacing={3}>
          {[...Array(4)].map((_, i) => (
            <Grid item xs={12} md={6} key={i}>
              <ChartSkeleton />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>Dashboard</Typography>
        <Paper sx={{ p: 4, textAlign: 'center', mt: 4 }}>
          <Typography variant="h6" color="error" gutterBottom>
            Error Loading Data
          </Typography>
          <Typography color="textSecondary" mb={2}>
            {error.message || 'Failed to load invoice data'}
          </Typography>
          <Button variant="contained" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </Paper>
      </Box>
    );
  }

  const StatCard = ({ title, value, icon, color = 'primary' }: any) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h5">
              {typeof value === 'number' && title.includes('Amount') ? 
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">
          Dashboard
        </Typography>
      </Box>

      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Invoices"
            value={stats.total}
            icon={<Receipt fontSize="large" />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Amount"
            value={stats.totalAmount}
            icon={<AttachMoney fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Paid Amount"
            value={stats.paidAmount}
            icon={<TrendingUp fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Overdue Invoices"
            value={stats.overdue}
            icon={<Schedule fontSize="large" />}
            color="error"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Invoice Status Breakdown
            </Typography>
            <Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Draft:</Typography>
                <Typography>{stats.draft}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Sent:</Typography>
                <Typography>{stats.sent}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Paid:</Typography>
                <Typography>{stats.paid}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Overdue:</Typography>
                <Typography color="error">{stats.overdue}</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Financial Summary
            </Typography>
            <Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Total Invoiced:</Typography>
                <AmountDisplay amount={stats.totalAmount} />
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Total Paid:</Typography>
                <AmountDisplay amount={stats.paidAmount} />
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Outstanding:</Typography>
                <AmountDisplay amount={stats.outstandingAmount} />
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Collection Rate:</Typography>
                <Typography>
                  {stats.totalAmount > 0 ? 
                    `${((stats.paidAmount / stats.totalAmount) * 100).toFixed(1)}%` : 
                    '0%'
                  }
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {stats.total > 0 ? (
        <>
          <Grid container spacing={3} mt={4}>
            <Grid item xs={12} lg={8}>
              <OptimizedCashFlowChart data={cashFlowData} />
            </Grid>
            <Grid item xs={12} lg={4}>
              <OptimizedOverdueChart data={overdueAnalysis} />
            </Grid>
          </Grid>

          <Grid container spacing={3} mt={2}>
            <Grid item xs={12}>
              <OptimizedCustomerRiskChart data={customerSegments} />
            </Grid>
          </Grid>
        </>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            No Invoice Data Available
          </Typography>
          <Typography color="textSecondary" mb={2}>
            Create your first invoice to see analytics and insights here.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default Dashboard;