import React, { useState } from 'react';
import {
  Box, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Typography, TextField, IconButton, Chip
} from '@mui/material';
import { Visibility, Search } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useCustomers } from '../hooks/useCustomers';
import AmountDisplay from '../components/AmountDisplay';
import { TableSkeleton } from '../components/LoadingSkeleton';
import { Customer } from '../types';

const CustomerList: React.FC = () => {
  const navigate = useNavigate();
  const { data: customers = [], isLoading, error } = useCustomers();
  const [searchTerm, setSearchTerm] = useState('');

  const filteredCustomers = Array.isArray(customers) ? customers.filter((customer: Customer) =>
    customer.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    customer.customer_email.toLowerCase().includes(searchTerm.toLowerCase())
  ) : [];

  const getRiskLevel = (customer: any) => {
    const outstandingRatio = customer.outstanding_amount / customer.total_amount;
    if (outstandingRatio > 0.7) return { level: 'High', color: 'error' };
    if (outstandingRatio > 0.3) return { level: 'Medium', color: 'warning' };
    return { level: 'Low', color: 'success' };
  };

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>Customers</Typography>
        <Box mb={3}>
          <TextField
            placeholder="Search customers..."
            disabled
            InputProps={{ startAdornment: <Search /> }}
            sx={{ minWidth: 300 }}
          />
        </Box>
        <Paper>
          <TableSkeleton />
        </Paper>
      </Box>
    );
  }
  if (error) return <Typography color="error">Error loading customers</Typography>;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Customers</Typography>
      </Box>

      <Box mb={3}>
        <TextField
          placeholder="Search customers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{ startAdornment: <Search /> }}
          sx={{ minWidth: 300 }}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Customer Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell align="right">Total Invoices</TableCell>
              <TableCell align="right">Total Amount</TableCell>
              <TableCell align="right">Paid Amount</TableCell>
              <TableCell align="right">Outstanding</TableCell>
              <TableCell align="center">Risk Level</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCustomers.map((customer: Customer) => {
              const risk = getRiskLevel(customer);
              return (
                <TableRow key={customer.customer_id} hover>
                  <TableCell>{customer.customer_name}</TableCell>
                  <TableCell>{customer.customer_email}</TableCell>
                  <TableCell align="right">{customer.total_invoices}</TableCell>
                  <TableCell align="right">
                    <AmountDisplay amount={customer.total_amount} />
                  </TableCell>
                  <TableCell align="right">
                    <AmountDisplay amount={customer.paid_amount} />
                  </TableCell>
                  <TableCell align="right">
                    <AmountDisplay amount={customer.outstanding_amount} />
                  </TableCell>
                  <TableCell align="center">
                    <Chip 
                      label={risk.level} 
                      color={risk.color as any} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton onClick={() => navigate(`/customers/${customer.customer_id}`)}>
                      <Visibility />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredCustomers.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography variant="h6" color="textSecondary">
            No customers found
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default CustomerList;