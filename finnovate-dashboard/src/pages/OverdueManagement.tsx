import React, { useState } from 'react';
import {
  Box, Paper, Typography, Button, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, IconButton, Alert
} from '@mui/material';
import { Refresh, Visibility, Email, Phone } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useInvoices } from '../hooks/useInvoices';
import StatusBadge from '../components/StatusBadge';
import AmountDisplay from '../components/AmountDisplay';

const OverdueManagement: React.FC = () => {
  const navigate = useNavigate();
  const { data: invoices = [], refetch } = useInvoices();
  const [isRunningCheck, setIsRunningCheck] = useState(false);

  const overdueInvoices = invoices.filter(invoice => {
    const now = new Date();
    const dueDate = new Date(invoice.due_date);
    return dueDate < now && invoice.remaining_balance > 0;
  });

  const getDaysPastDue = (dueDate: string) => {
    const now = new Date();
    const due = new Date(dueDate);
    return Math.floor((now.getTime() - due.getTime()) / (1000 * 60 * 60 * 24));
  };

  const getPriorityLevel = (daysPastDue: number) => {
    if (daysPastDue > 60) return { level: 'Critical', color: 'error' };
    if (daysPastDue > 30) return { level: 'High', color: 'warning' };
    return { level: 'Medium', color: 'info' };
  };

  const runOverdueCheck = async () => {
    setIsRunningCheck(true);
    try {
      // In a real app, this would call the backend overdue check endpoint
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      await refetch();
    } catch (error) {
      console.error('Failed to run overdue check:', error);
    } finally {
      setIsRunningCheck(false);
    }
  };

  const totalOverdueAmount = overdueInvoices.reduce((sum, inv) => sum + inv.remaining_balance, 0);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Overdue Management</Typography>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={runOverdueCheck}
          disabled={isRunningCheck}
        >
          {isRunningCheck ? 'Running Check...' : 'Run Overdue Check'}
        </Button>
      </Box>

      <Alert severity="warning" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>{overdueInvoices.length}</strong> overdue invoices totaling{' '}
          <AmountDisplay amount={totalOverdueAmount} variant="body2" />
        </Typography>
      </Alert>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Invoice #</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Due Date</TableCell>
              <TableCell>Days Past Due</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell align="right">Outstanding</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {overdueInvoices.map((invoice) => {
              const daysPastDue = getDaysPastDue(invoice.due_date);
              const priority = getPriorityLevel(daysPastDue);
              
              return (
                <TableRow key={invoice.invoice_id} hover>
                  <TableCell>{invoice.invoice_number}</TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2">{invoice.customer_name}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        {invoice.customer_email}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{new Date(invoice.due_date).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <Typography color="error.main" fontWeight="bold">
                      {daysPastDue} days
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={priority.level} 
                      color={priority.color as any} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell align="right">
                    <AmountDisplay amount={invoice.remaining_balance} />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton onClick={() => navigate(`/invoices/${invoice.invoice_id}`)}>
                      <Visibility />
                    </IconButton>
                    <IconButton color="primary" title="Send Reminder Email">
                      <Email />
                    </IconButton>
                    <IconButton color="secondary" title="Call Customer">
                      <Phone />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {overdueInvoices.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography variant="h6" color="success.main">
            🎉 No overdue invoices found!
          </Typography>
          <Typography variant="body2" color="textSecondary">
            All invoices are current or paid.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default OverdueManagement;