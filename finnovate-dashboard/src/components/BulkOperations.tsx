import React, { useState } from 'react';
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, TextField, Typography,
  List, ListItem, ListItemText, Checkbox
} from '@mui/material';
import { useUpdateInvoiceStatus } from '../hooks/useInvoices';
import { Invoice, InvoiceStatus } from '../types';
import AmountDisplay from './AmountDisplay';

interface BulkOperationsProps {
  selectedInvoices: Invoice[];
  onClose: () => void;
  onSuccess: () => void;
}

const BulkOperations: React.FC<BulkOperationsProps> = ({ 
  selectedInvoices, 
  onClose, 
  onSuccess 
}) => {
  const updateStatus = useUpdateInvoiceStatus();
  const [operation, setOperation] = useState('');
  const [newStatus, setNewStatus] = useState<InvoiceStatus>('SENT');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleBulkStatusUpdate = async () => {
    setIsProcessing(true);
    try {
      for (const invoice of selectedInvoices) {
        await updateStatus.mutateAsync({
          invoiceId: invoice.invoice_id,
          status: newStatus,
        });
      }
      onSuccess();
      onClose();
    } catch (error) {
      alert('Failed to update invoice statuses');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBulkPayment = async () => {
    const amount = parseFloat(paymentAmount);
    if (!amount || amount <= 0) {
      alert('Please enter a valid payment amount');
      return;
    }

    setIsProcessing(true);
    try {
      // In a real app, this would call a bulk payment API
      for (const invoice of selectedInvoices) {
        if (amount <= invoice.remaining_balance) {
          // Process payment for each invoice
          console.log(`Processing payment of ${amount} for invoice ${invoice.invoice_id}`);
        }
      }
      onSuccess();
      onClose();
    } catch (error) {
      alert('Failed to process bulk payments');
    } finally {
      setIsProcessing(false);
    }
  };

  const canUpdateStatus = (status: InvoiceStatus) => {
    return selectedInvoices.every(invoice => {
      switch (invoice.status) {
        case 'DRAFT': return status === 'SENT';
        case 'SENT': return status === 'PAID';
        case 'OVERDUE': return status === 'PAID';
        default: return false;
      }
    });
  };

  const totalAmount = selectedInvoices.reduce((sum, inv) => sum + inv.remaining_balance, 0);

  return (
    <Dialog open={selectedInvoices.length > 0} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Bulk Operations ({selectedInvoices.length} invoices selected)
      </DialogTitle>
      <DialogContent>
        <Box mb={3}>
          <Typography variant="subtitle2" gutterBottom>
            Selected Invoices:
          </Typography>
          <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
            {selectedInvoices.map((invoice) => (
              <ListItem key={invoice.invoice_id}>
                <ListItemText
                  primary={`${invoice.invoice_number} - ${invoice.customer_name}`}
                  secondary={
                    <Box display="flex" justifyContent="space-between">
                      <span>Status: {invoice.status}</span>
                      <AmountDisplay amount={invoice.remaining_balance} variant="body2" />
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
          <Typography variant="body2" color="textSecondary" mt={1}>
            Total Outstanding: <AmountDisplay amount={totalAmount} variant="body2" />
          </Typography>
        </Box>

        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Operation</InputLabel>
          <Select
            value={operation}
            onChange={(e) => setOperation(e.target.value)}
            label="Operation"
          >
            <MenuItem value="status">Update Status</MenuItem>
            <MenuItem value="payment">Record Payment</MenuItem>
          </Select>
        </FormControl>

        {operation === 'status' && (
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>New Status</InputLabel>
            <Select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value as InvoiceStatus)}
              label="New Status"
            >
              <MenuItem value="SENT" disabled={!canUpdateStatus('SENT')}>
                Sent
              </MenuItem>
              <MenuItem value="PAID" disabled={!canUpdateStatus('PAID')}>
                Paid
              </MenuItem>
            </Select>
          </FormControl>
        )}

        {operation === 'payment' && (
          <TextField
            fullWidth
            label="Payment Amount (per invoice)"
            type="number"
            value={paymentAmount}
            onChange={(e) => setPaymentAmount(e.target.value)}
            inputProps={{ min: 0, step: 0.01 }}
            sx={{ mb: 2 }}
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={operation === 'status' ? handleBulkStatusUpdate : handleBulkPayment}
          disabled={!operation || isProcessing}
        >
          {isProcessing ? 'Processing...' : 'Apply'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BulkOperations;