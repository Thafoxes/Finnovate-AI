import React from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';
import { useInvoices } from '../hooks/useInvoices';
import AmountDisplay from './AmountDisplay';

const DSOTracker: React.FC = () => {
  const { data: invoices = [] } = useInvoices();

  const calculateDSO = () => {
    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - (30 * 24 * 60 * 60 * 1000));
    
    // Get invoices from the last 30 days
    const recentInvoices = invoices.filter(inv => 
      new Date(inv.issue_date) >= thirtyDaysAgo
    );
    
    if (recentInvoices.length === 0) return { current: 0, previous: 0, trend: 'flat' };
    
    // Calculate current DSO
    const totalReceivables = recentInvoices.reduce((sum, inv) => sum + inv.remaining_balance, 0);
    const totalSales = recentInvoices.reduce((sum, inv) => sum + inv.total_amount, 0);
    const currentDSO = totalSales > 0 ? (totalReceivables / totalSales) * 30 : 0;
    
    // Calculate previous period DSO (30-60 days ago)
    const sixtyDaysAgo = new Date(now.getTime() - (60 * 24 * 60 * 60 * 1000));
    const previousInvoices = invoices.filter(inv => {
      const issueDate = new Date(inv.issue_date);
      return issueDate >= sixtyDaysAgo && issueDate < thirtyDaysAgo;
    });
    
    const prevTotalReceivables = previousInvoices.reduce((sum, inv) => sum + inv.remaining_balance, 0);
    const prevTotalSales = previousInvoices.reduce((sum, inv) => sum + inv.total_amount, 0);
    const previousDSO = prevTotalSales > 0 ? (prevTotalReceivables / prevTotalSales) * 30 : 0;
    
    let trend = 'flat';
    if (currentDSO > previousDSO) trend = 'up';
    else if (currentDSO < previousDSO) trend = 'down';
    
    return { current: currentDSO, previous: previousDSO, trend };
  };

  const calculateCollectionEffectiveness = () => {
    const paidInvoices = invoices.filter(inv => inv.paid_amount > 0);
    if (paidInvoices.length === 0) return 0;
    
    const totalCollected = paidInvoices.reduce((sum, inv) => sum + inv.paid_amount, 0);
    const totalInvoiced = paidInvoices.reduce((sum, inv) => sum + inv.total_amount, 0);
    
    return totalInvoiced > 0 ? (totalCollected / totalInvoiced) * 100 : 0;
  };

  const calculateOverdueRate = () => {
    const now = new Date();
    const overdueInvoices = invoices.filter(inv => {
      const dueDate = new Date(inv.due_date);
      return dueDate < now && inv.remaining_balance > 0;
    });
    
    return invoices.length > 0 ? (overdueInvoices.length / invoices.length) * 100 : 0;
  };

  const dsoData = calculateDSO();
  const collectionEffectiveness = calculateCollectionEffectiveness();
  const overdueRate = calculateOverdueRate();

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp color="error" />;
      case 'down': return <TrendingDown color="success" />;
      default: return <TrendingFlat color="action" />;
    }
  };

  const KPICard = ({ title, value, suffix = '', trend, color = 'primary' }: any) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h5" color={color}>
              {typeof value === 'number' ? value.toFixed(1) : value}{suffix}
            </Typography>
          </Box>
          {trend && (
            <Box>
              {getTrendIcon(trend)}
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Financial KPIs
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Days Sales Outstanding"
            value={dsoData.current}
            suffix=" days"
            trend={dsoData.trend}
            color={dsoData.current > 30 ? 'error.main' : 'success.main'}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Collection Effectiveness"
            value={collectionEffectiveness}
            suffix="%"
            color={collectionEffectiveness > 80 ? 'success.main' : 'warning.main'}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Overdue Rate"
            value={overdueRate}
            suffix="%"
            color={overdueRate < 10 ? 'success.main' : 'error.main'}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Total Outstanding"
            value={<AmountDisplay amount={invoices.reduce((sum, inv) => sum + inv.remaining_balance, 0)} variant="h6" />}
            color="primary.main"
          />
        </Grid>
      </Grid>
    </Paper>
  );
};

export default DSOTracker;