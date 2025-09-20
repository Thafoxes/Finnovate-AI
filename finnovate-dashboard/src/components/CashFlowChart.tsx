import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useInvoices } from '../hooks/useInvoices';

const CashFlowChart: React.FC = () => {
  const { data: invoices = [] } = useInvoices();

  // Generate cash flow data for the last 6 months
  const generateCashFlowData = () => {
    const months = [];
    const now = new Date();
    
    for (let i = 5; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthKey = date.toISOString().slice(0, 7); // YYYY-MM format
      const monthName = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      
      const monthInvoices = invoices.filter(inv => 
        inv.issue_date.startsWith(monthKey)
      );
      
      const invoiced = monthInvoices.reduce((sum, inv) => sum + inv.total_amount, 0);
      const collected = monthInvoices.reduce((sum, inv) => sum + inv.paid_amount, 0);
      const outstanding = invoiced - collected;
      
      months.push({
        month: monthName,
        invoiced,
        collected,
        outstanding,
      });
    }
    
    return months;
  };

  const data = generateCashFlowData();

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
        Cash Flow Trend
      </Typography>
      <Box height={300}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={formatCurrency} />
            <Tooltip formatter={(value: number) => formatCurrency(value)} />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="invoiced" 
              stroke="#1976d2" 
              strokeWidth={2}
              name="Invoiced"
            />
            <Line 
              type="monotone" 
              dataKey="collected" 
              stroke="#2e7d32" 
              strokeWidth={2}
              name="Collected"
            />
            <Line 
              type="monotone" 
              dataKey="outstanding" 
              stroke="#ed6c02" 
              strokeWidth={2}
              name="Outstanding"
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
};

export default CashFlowChart;