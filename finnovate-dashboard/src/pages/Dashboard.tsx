import React from 'react';
import { Box, Grid, Paper, Typography, Card, CardContent } from '@mui/material';
import { Receipt, AttachMoney, Schedule, TrendingUp } from '@mui/icons-material';
import { useInvoices } from '../hooks/useInvoices';
import { useOptimizedInvoiceData } from '../hooks/useOptimizedData';
import AmountDisplay from '../components/AmountDisplay';
import CustomerStats from '../components/CustomerStats';
import LoadingSpinner from '../components/LoadingSpinner';
import DSOTracker from '../components/DSOTracker';
import CashFlowChart from '../components/CashFlowChart';
import PaymentTrendsChart from '../components/PaymentTrendsChart';
import OverdueAnalysis from '../components/OverdueAnalysis';
import CustomerSegmentChart from '../components/CustomerSegmentChart';

const Dashboard: React.FC = () => {
  const { data: invoices = [], isLoading } = useInvoices();
  const { stats } = useOptimizedInvoiceData(invoices);

  if (isLoading) {
    return <LoadingSpinner message="Loading dashboard..." variant="skeleton" rows={6} />;
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
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

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

      <Box mt={4}>
        <CustomerStats />
      </Box>

      <Box mt={4}>
        <DSOTracker />
      </Box>

      <Grid container spacing={3} mt={2}>
        <Grid item xs={12} lg={8}>
          <CashFlowChart />
        </Grid>
        <Grid item xs={12} lg={4}>
          <PaymentTrendsChart />
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={2}>
        <Grid item xs={12} lg={6}>
          <OverdueAnalysis />
        </Grid>
        <Grid item xs={12} lg={6}>
          <CustomerSegmentChart />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;