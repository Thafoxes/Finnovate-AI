import React, { useState } from 'react';
import {
  Box, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button, TextField, MenuItem, IconButton, Typography, Fab
} from '@mui/material';
import { Add, Edit, Delete, Visibility, Search } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useInvoices, useDeleteInvoice } from '../hooks/useInvoices';
import StatusBadge from '../components/StatusBadge';
import AmountDisplay from '../components/AmountDisplay';
import { InvoiceStatus } from '../types';

const InvoiceList: React.FC = () => {
  const navigate = useNavigate();
  const { data: invoices = [], isLoading, error } = useInvoices();
  const deleteInvoice = useDeleteInvoice();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | ''>('');

  const filteredInvoices = invoices.filter(invoice => {
    const matchesSearch = invoice.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !statusFilter || invoice.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDelete = async (invoiceId: string, status: InvoiceStatus) => {
    if (status !== 'DRAFT') {
      alert('Only DRAFT invoices can be deleted');
      return;
    }
    if (window.confirm('Are you sure you want to delete this invoice?')) {
      try {
        await deleteInvoice.mutateAsync(invoiceId);
      } catch (error) {
        alert('Failed to delete invoice');
      }
    }
  };

  if (isLoading) return <Typography>Loading invoices...</Typography>;
  if (error) return <Typography color="error">Error loading invoices</Typography>;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Invoices</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => navigate('/invoices/create')}
        >
          Create Invoice
        </Button>
      </Box>

      <Box display="flex" gap={2} mb={3}>
        <TextField
          placeholder="Search invoices..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{ startAdornment: <Search /> }}
          sx={{ minWidth: 300 }}
        />
        <TextField
          select
          label="Status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as InvoiceStatus | '')}
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="">All Status</MenuItem>
          <MenuItem value="DRAFT">Draft</MenuItem>
          <MenuItem value="SENT">Sent</MenuItem>
          <MenuItem value="PAID">Paid</MenuItem>
          <MenuItem value="OVERDUE">Overdue</MenuItem>
        </TextField>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Invoice #</TableCell>
              <TableCell>Customer</TableCell>
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
            {filteredInvoices.map((invoice) => (
              <TableRow key={invoice.invoice_id} hover>
                <TableCell>{invoice.invoice_number}</TableCell>
                <TableCell>{invoice.customer_name}</TableCell>
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
                  {invoice.status === 'DRAFT' && (
                    <IconButton onClick={() => navigate(`/invoices/${invoice.invoice_id}/edit`)}>
                      <Edit />
                    </IconButton>
                  )}
                  {invoice.status === 'DRAFT' && (
                    <IconButton 
                      onClick={() => handleDelete(invoice.invoice_id, invoice.status)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredInvoices.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography variant="h6" color="textSecondary">
            No invoices found
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default InvoiceList;