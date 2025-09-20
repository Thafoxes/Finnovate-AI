import React from 'react';
import {
  Box, Paper, Typography, Grid, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, IconButton
} from '@mui/material';
import { Visibility } from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useCustomer, useCustomerInvoices } from '../hooks/useCustomers';
import AmountDisplay from '../components/AmountDisplay';
import StatusBadge from '../components/StatusBadge';

const CustomerProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: customer, isLoading: customerLoading } = useCustomer(id!);
  const { data: invoices = [], isLoading: invoicesLoading } = useCustomerInvoices(id!);

  if (customerLoading) return <Typography>Loading customer...</Typography>;
  if (!customer) return <Typography color="error">Customer not found</Typography>;

  const getRiskLevel = () => {
    const outstandingRatio = customer.outstanding_amount / customer.total_amount;
    if (outstandingRatio > 0.7) return { level: 'High Risk', color: 'error' };
    if (outstandingRatio > 0.3) return { level: 'Medium Risk', color: 'warning' };
    return { level: 'Low Risk', color: 'success' };
  };

  const risk = getRiskLevel();
  const collectionRate = customer.total_amount > 0 ? 
    ((customer.paid_amount / customer.total_amount) * 100).toFixed(1) : '0';

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Customer Profile
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Customer Information</Typography>
            <Typography><strong>Name:</strong> {customer.customer_name}</Typography>
            <Typography><strong>Email:</strong> {customer.customer_email}</Typography>
            <Typography><strong>Customer ID:</strong> {customer.customer_id}</Typography>
            <Box mt={2}>
              <Chip 
                label={risk.level} 
                color={risk.color as any} 
                size="medium"
              />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Financial Summary</Typography>
            <Box display="flex" justifyContent="space-between" py={1}>
              <Typography>Total Invoices:</Typography>
              <Typography>{customer.total_invoices}</Typography>
            </Box>
            <Box display="flex" justifyContent="space-between" py={1}>
              <Typography>Total Amount:</Typography>
              <AmountDisplay amount={customer.total_amount} />
            </Box>
            <Box display="flex" justifyContent="space-between" py={1}>
              <Typography>Paid Amount:</Typography>
              <AmountDisplay amount={customer.paid_amount} />
            </Box>
            <Box display="flex" justifyContent="space-between" py={1}>
              <Typography>Outstanding:</Typography>
              <AmountDisplay amount={customer.outstanding_amount} />
            </Box>
            <Box display="flex" justifyContent="space-between" py={1}>
              <Typography>Collection Rate:</Typography>
              <Typography>{collectionRate}%</Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Box mt={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Invoice History</Typography>
          
          {invoicesLoading ? (
            <Typography>Loading invoices...</Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Invoice #</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Issue Date</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Paid</TableCell>
                    <TableCell align="right">Balance</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {invoices.map((invoice) => (
                    <TableRow key={invoice.invoice_id} hover>
                      <TableCell>{invoice.invoice_number}</TableCell>
                      <TableCell><StatusBadge status={invoice.status} /></TableCell>
                      <TableCell>{new Date(invoice.issue_date).toLocaleDateString()}</TableCell>
                      <TableCell>{new Date(invoice.due_date).toLocaleDateString()}</TableCell>
                      <TableCell align="right">
                        <AmountDisplay amount={invoice.total_amount} />
                      </TableCell>
                      <TableCell align="right">
                        <AmountDisplay amount={invoice.paid_amount} />
                      </TableCell>
                      <TableCell align="right">
                        <AmountDisplay amount={invoice.remaining_balance} />
                      </TableCell>
                      <TableCell align="center">
                        <IconButton onClick={() => navigate(`/invoices/${invoice.invoice_id}`)}>
                          <Visibility />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {invoices.length === 0 && !invoicesLoading && (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="textSecondary">
                No invoices found for this customer
              </Typography>
            </Box>
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default CustomerProfile;