import React, { useState } from 'react';
import {
  Box, Paper, Typography, Button, Grid, Divider, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, MenuItem
} from '@mui/material';
import { Edit, Delete, Payment, Send } from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useInvoice, useUpdateInvoiceStatus, useDeleteInvoice } from '../hooks/useInvoices';
import StatusBadge from '../components/StatusBadge';
import AmountDisplay from '../components/AmountDisplay';
import PaymentModal from '../components/PaymentModal';
import PaymentHistory from '../components/PaymentHistory';
import { InvoiceStatus } from '../types';

const InvoiceDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: invoice, isLoading, error } = useInvoice(id!);
  const updateStatus = useUpdateInvoiceStatus();
  const deleteInvoice = useDeleteInvoice();

  const [paymentDialog, setPaymentDialog] = useState(false);
  const [statusDialog, setStatusDialog] = useState(false);
  const [newStatus, setNewStatus] = useState<InvoiceStatus>('SENT');

  if (isLoading) return <Typography>Loading invoice...</Typography>;
  if (error || !invoice) return <Typography color="error">Invoice not found</Typography>;

  const handleStatusUpdate = async () => {
    try {
      await updateStatus.mutateAsync({ invoiceId: invoice.invoice_id, status: newStatus });
      setStatusDialog(false);
    } catch (error) {
      alert('Failed to update status');
    }
  };



  const handleDelete = async () => {
    if (invoice.status !== 'DRAFT') {
      alert('Only DRAFT invoices can be deleted');
      return;
    }
    if (window.confirm('Are you sure you want to delete this invoice?')) {
      try {
        await deleteInvoice.mutateAsync(invoice.invoice_id);
        navigate('/invoices');
      } catch (error) {
        alert('Failed to delete invoice');
      }
    }
  };

  const getValidStatusTransitions = (currentStatus: InvoiceStatus): InvoiceStatus[] => {
    switch (currentStatus) {
      case 'DRAFT': return ['SENT'];
      case 'SENT': return ['PAID'];
      case 'OVERDUE': return ['PAID'];
      default: return [];
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Invoice Details</Typography>
        <Box>
          {invoice.status === 'DRAFT' && (
            <Button
              variant="outlined"
              startIcon={<Edit />}
              onClick={() => navigate(`/invoices/${invoice.invoice_id}/edit`)}
              sx={{ mr: 1 }}
            >
              Edit
            </Button>
          )}
          {getValidStatusTransitions(invoice.status).length > 0 && (
            <Button
              variant="outlined"
              startIcon={<Send />}
              onClick={() => setStatusDialog(true)}
              sx={{ mr: 1 }}
            >
              Update Status
            </Button>
          )}
          {invoice.remaining_balance > 0 && invoice.status !== 'DRAFT' && (
            <Button
              variant="contained"
              startIcon={<Payment />}
              onClick={() => setPaymentDialog(true)}
              sx={{ mr: 1 }}
            >
              Process Payment
            </Button>
          )}
          {invoice.status === 'DRAFT' && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<Delete />}
              onClick={handleDelete}
            >
              Delete
            </Button>
          )}
        </Box>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>Invoice Information</Typography>
            <Typography><strong>Invoice #:</strong> {invoice.invoice_number}</Typography>
            <Typography><strong>Status:</strong> <StatusBadge status={invoice.status} /></Typography>
            <Typography><strong>Issue Date:</strong> {new Date(invoice.issue_date).toLocaleDateString()}</Typography>
            <Typography><strong>Due Date:</strong> {new Date(invoice.due_date).toLocaleDateString()}</Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>Customer Information</Typography>
            <Typography><strong>Name:</strong> {invoice.customer_name}</Typography>
            <Typography><strong>Email:</strong> {invoice.customer_email}</Typography>
            <Typography><strong>Customer ID:</strong> {invoice.customer_id}</Typography>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>Line Items</Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Description</TableCell>
                <TableCell align="right">Quantity</TableCell>
                <TableCell align="right">Unit Price</TableCell>
                <TableCell align="right">Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoice.line_items.map((item, index) => (
                <TableRow key={index}>
                  <TableCell>{item.description}</TableCell>
                  <TableCell align="right">{item.quantity}</TableCell>
                  <TableCell align="right"><AmountDisplay amount={item.unit_price} /></TableCell>
                  <TableCell align="right"><AmountDisplay amount={item.total} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Divider sx={{ my: 3 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>Payment Summary</Typography>
            <Typography><strong>Subtotal:</strong> <AmountDisplay amount={invoice.subtotal} /></Typography>
            <Typography><strong>Total Amount:</strong> <AmountDisplay amount={invoice.total_amount} /></Typography>
            <Typography><strong>Paid Amount:</strong> <AmountDisplay amount={invoice.paid_amount} /></Typography>
            <Typography><strong>Remaining Balance:</strong> <AmountDisplay amount={invoice.remaining_balance} /></Typography>
          </Grid>
        </Grid>
      </Paper>

      <Box mt={3}>
        <PaymentHistory invoiceId={invoice.invoice_id} />
      </Box>

      <PaymentModal
        open={paymentDialog}
        onClose={() => setPaymentDialog(false)}
        invoice={{
          invoice_id: invoice.invoice_id,
          invoice_number: invoice.invoice_number,
          remaining_balance: invoice.remaining_balance,
        }}
      />

      {/* Status Update Dialog */}
      <Dialog open={statusDialog} onClose={() => setStatusDialog(false)}>
        <DialogTitle>Update Invoice Status</DialogTitle>
        <DialogContent>
          <TextField
            select
            fullWidth
            label="New Status"
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value as InvoiceStatus)}
            sx={{ mt: 2 }}
          >
            {getValidStatusTransitions(invoice.status).map((status) => (
              <MenuItem key={status} value={status}>{status}</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatusDialog(false)}>Cancel</Button>
          <Button onClick={handleStatusUpdate} variant="contained">Update Status</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InvoiceDetails;