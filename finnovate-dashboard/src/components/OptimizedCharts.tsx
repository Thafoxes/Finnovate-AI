import React, { memo } from 'react';
import { Paper, Typography, Box } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface CashFlowData {
  month: string;
  invoiced: number;
  paid: number;
  outstanding: number;
  collectionRate: number;
  [key: string]: string | number;
}

interface OverdueData {
  category: string;
  count: number;
  amount: number;
  [key: string]: string | number;
}

interface CustomerSegment {
  customer_id: string;
  customer_name: string;
  totalAmount: number;
  riskScore: number;
  [key: string]: string | number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export const OptimizedCashFlowChart = memo(({ data }: { data: CashFlowData[] }) => (
  <Paper sx={{ p: 3 }}>
    <Typography variant="h6" gutterBottom>Cash Flow Trends</Typography>
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, '']} />
        <Bar dataKey="invoiced" fill="#8884d8" name="Invoiced" />
        <Bar dataKey="paid" fill="#82ca9d" name="Paid" />
      </BarChart>
    </ResponsiveContainer>
  </Paper>
));

export const OptimizedOverdueChart = memo(({ data }: { data: OverdueData[] }) => (
  <Paper sx={{ p: 3 }}>
    <Typography variant="h6" gutterBottom>Overdue Analysis</Typography>
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ category, count }) => `${category}: ${count}`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="amount"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, 'Amount']} />
      </PieChart>
    </ResponsiveContainer>
  </Paper>
));

export const OptimizedCustomerRiskChart = memo(({ data }: { data: CustomerSegment[] }) => {
  const topRiskCustomers = data
    .filter(c => c.riskScore > 0)
    .sort((a, b) => b.riskScore - a.riskScore)
    .slice(0, 5);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>Top Risk Customers</Typography>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={topRiskCustomers} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="customer_name" type="category" width={100} />
          <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, 'Risk Score']} />
          <Bar dataKey="riskScore" fill="#ff7300" />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
});