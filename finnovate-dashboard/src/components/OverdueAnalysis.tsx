import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useInvoices } from '../hooks/useInvoices';
import AmountDisplay from './AmountDisplay';

const OverdueAnalysis: React.FC = () => {
  const { data: invoices = [] } = useInvoices();

  const generateOverdueData = () => {
    const now = new Date();
    const categories = {
      current: { count: 0, amount: 0, color: '#2e7d32' },
      overdue1to30: { count: 0, amount: 0, color: '#ed6c02' },
      overdue31to60: { count: 0, amount: 0, color: '#d32f2f' },
      overdue60plus: { count: 0, amount: 0, color: '#9c27b0' },
    };

    invoices.forEach(invoice => {
      if (invoice.remaining_balance <= 0) return;

      const dueDate = new Date(invoice.due_date);
      const daysPastDue = Math.floor((now.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24));

      if (daysPastDue <= 0) {
        categories.current.count++;
        categories.current.amount += invoice.remaining_balance;
      } else if (daysPastDue <= 30) {
        categories.overdue1to30.count++;
        categories.overdue1to30.amount += invoice.remaining_balance;
      } else if (daysPastDue <= 60) {
        categories.overdue31to60.count++;
        categories.overdue31to60.amount += invoice.remaining_balance;
      } else {
        categories.overdue60plus.count++;
        categories.overdue60plus.amount += invoice.remaining_balance;
      }
    });

    return [
      { name: 'Current', value: categories.current.amount, count: categories.current.count, color: categories.current.color },
      { name: '1-30 Days', value: categories.overdue1to30.amount, count: categories.overdue1to30.count, color: categories.overdue1to30.color },
      { name: '31-60 Days', value: categories.overdue31to60.amount, count: categories.overdue31to60.count, color: categories.overdue31to60.color },
      { name: '60+ Days', value: categories.overdue60plus.amount, count: categories.overdue60plus.count, color: categories.overdue60plus.color },
    ].filter(item => item.value > 0);
  };

  const data = generateOverdueData();
  const totalOverdue = data.reduce((sum, item) => sum + item.value, 0);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-MY', {
      style: 'currency',
      currency: 'MYR',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box sx={{ bgcolor: 'background.paper', p: 1, border: 1, borderColor: 'divider', borderRadius: 1 }}>
          <Typography variant="body2">{data.name}</Typography>
          <Typography variant="body2">Amount: {formatCurrency(data.value)}</Typography>
          <Typography variant="body2">Invoices: {data.count}</Typography>
        </Box>
      );
    }
    return null;
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Overdue Analysis
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Box height={250}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </Box>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle1" gutterBottom>
            Summary
          </Typography>
          {data.map((item, index) => (
            <Box key={index} display="flex" justifyContent="space-between" py={0.5}>
              <Box display="flex" alignItems="center">
                <Box 
                  width={12} 
                  height={12} 
                  bgcolor={item.color} 
                  borderRadius="50%" 
                  mr={1}
                />
                <Typography variant="body2">{item.name}:</Typography>
              </Box>
              <Typography variant="body2">
                <AmountDisplay amount={item.value} variant="body2" /> ({item.count})
              </Typography>
            </Box>
          ))}
          <Box display="flex" justifyContent="space-between" py={1} mt={1} borderTop={1} borderColor="divider">
            <Typography variant="subtitle2">Total Outstanding:</Typography>
            <Typography variant="subtitle2">
              <AmountDisplay amount={totalOverdue} variant="subtitle1" />
            </Typography>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default OverdueAnalysis;