import React from 'react';
import { Box, Grid, Paper, Typography, Card, CardContent } from '@mui/material';
import { Receipt, AttachMoney, Schedule, TrendingUp } from '@mui/icons-material';
import { useInvoices } from '../hooks/useInvoices';
import AmountDisplay from '../components/AmountDisplay';

const Dashboard: React.FC = () => {
  const { data: invoices = [] } = useInvoices();

  const stats = {
    totalInvoices: invoices.length,
    totalAmount: invoices.reduce((sum, inv) => sum + inv.total_amount, 0),
    paidAmount: invoices.reduce((sum, inv) => sum + inv.paid_amount, 0),
    overdueCount: invoices.filter(inv => inv.status === 'OVERDUE').length,
    draftCount: invoices.filter(inv => inv.status === 'DRAFT').length,
    sentCount: invoices.filter(inv => inv.status === 'SENT').length,
    paidCount: invoices.filter(inv => inv.status === 'PAID').length,
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
            value={stats.totalInvoices}
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
            value={stats.overdueCount}
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
                <Typography>{stats.draftCount}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Sent:</Typography>
                <Typography>{stats.sentCount}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Paid:</Typography>
                <Typography>{stats.paidCount}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Overdue:</Typography>
                <Typography color="error">{stats.overdueCount}</Typography>
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
                <AmountDisplay amount={stats.totalAmount - stats.paidAmount} />
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
    </Box>
  );
};

export default Dashboard;