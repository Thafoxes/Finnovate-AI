import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useCustomers } from '../hooks/useCustomers';

const CustomerSegmentChart: React.FC = () => {
  const { data: customers = [] } = useCustomers();

  const generateSegmentData = () => {
    const segments = {
      'High Value': { count: 0, totalAmount: 0, collectionRate: 0 },
      'Medium Value': { count: 0, totalAmount: 0, collectionRate: 0 },
      'Low Value': { count: 0, totalAmount: 0, collectionRate: 0 },
    };

    customers.forEach(customer => {
      let segment = 'Low Value';
      if (customer.total_amount > 50000) segment = 'High Value';
      else if (customer.total_amount > 10000) segment = 'Medium Value';

      segments[segment as keyof typeof segments].count++;
      segments[segment as keyof typeof segments].totalAmount += customer.total_amount;
      
      const rate = customer.total_amount > 0 ? (customer.paid_amount / customer.total_amount) * 100 : 0;
      segments[segment as keyof typeof segments].collectionRate += rate;
    });

    // Calculate average collection rates
    Object.keys(segments).forEach(key => {
      const segment = segments[key as keyof typeof segments];
      if (segment.count > 0) {
        segment.collectionRate = segment.collectionRate / segment.count;
      }
    });

    return Object.entries(segments).map(([segment, data]) => ({
      segment,
      customers: data.count,
      totalAmount: data.totalAmount,
      collectionRate: data.collectionRate,
    }));
  };

  const data = generateSegmentData();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-MY', {
      style: 'currency',
      currency: 'MYR',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box sx={{ bgcolor: 'background.paper', p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
          <Typography variant="subtitle2">{label}</Typography>
          <Typography variant="body2">Customers: {data.customers}</Typography>
          <Typography variant="body2">Total Amount: {formatCurrency(data.totalAmount)}</Typography>
          <Typography variant="body2">Collection Rate: {data.collectionRate.toFixed(1)}%</Typography>
        </Box>
      );
    }
    return null;
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Customer Segments Performance
      </Typography>
      <Box height={300}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="segment" />
            <YAxis yAxisId="left" orientation="left" tickFormatter={formatCurrency} />
            <YAxis yAxisId="right" orientation="right" domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Bar yAxisId="left" dataKey="totalAmount" fill="#1976d2" name="Total Amount" />
            <Bar yAxisId="right" dataKey="collectionRate" fill="#2e7d32" name="Collection Rate %" />
          </BarChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
};

export default CustomerSegmentChart;