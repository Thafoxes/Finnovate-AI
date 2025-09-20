import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useInvoices } from '../hooks/useInvoices';

const PaymentTrendsChart: React.FC = () => {
  const { data: invoices = [] } = useInvoices();

  // Generate payment trends data for the last 30 days
  const generatePaymentTrends = () => {
    const days = [];
    const now = new Date();
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      const dateKey = date.toISOString().slice(0, 10); // YYYY-MM-DD format
      const dayName = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      
      // For demo purposes, we'll simulate payment data based on paid invoices
      const dayPayments = invoices.filter(inv => 
        inv.paid_amount > 0 && inv.updated_at.startsWith(dateKey)
      );
      
      const amount = dayPayments.reduce((sum, inv) => sum + inv.paid_amount, 0);
      const count = dayPayments.length;
      
      days.push({
        date: dayName,
        amount,
        count,
      });
    }
    
    return days;
  };

  const data = generatePaymentTrends();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-MY', {
      style: 'currency',
      currency: 'MYR',
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Payment Trends (Last 30 Days)
      </Typography>
      <Box height={300}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis tickFormatter={formatCurrency} />
            <Tooltip formatter={(value: number) => formatCurrency(value)} />
            <Bar dataKey="amount" fill="#1976d2" />
          </BarChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
};

export default PaymentTrendsChart;