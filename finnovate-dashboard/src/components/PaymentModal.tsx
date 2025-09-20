import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Button, Typography, Box, MenuItem, Alert
} from '@mui/material';
import toast from 'react-hot-toast';
import { useProcessPayment } from '../hooks/useInvoices';
import AmountDisplay from './AmountDisplay';
import PaymentReceipt from './PaymentReceipt';
import HelpTooltip from './HelpTooltip';
import { Payment } from '../types';

interface PaymentModalProps {
  open: boolean;
  onClose: () => void;
  invoice: {
    invoice_id: string;
    invoice_number: string;
    remaining_balance: number;
  };
}

const PaymentModal: React.FC<PaymentModalProps> = ({ open, onClose, invoice }) => {
  const processPayment = useProcessPayment();
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('');
  const [notes, setNotes] = useState('');
  const [showReceipt, setShowReceipt] = useState(false);
  const [lastPayment, setLastPayment] = useState<Payment | null>(null);
  const [mounted, setMounted] = useState(false);
  
  React.useEffect(() => {
    setMounted(true);
  }, []);
  
  if (!mounted) {
    return null;
  }

  const handleSubmit = async () => {
    const paymentAmount = parseFloat(amount);
    
    if (!paymentAmount || paymentAmount <= 0) {
      alert('Please enter a valid payment amount');
      return;
    }
    
    if (paymentAmount > invoice.remaining_balance) {
      alert('Payment amount cannot exceed remaining balance');
      return;
    }

    try {
      const result = await processPayment.mutateAsync({
        invoice_id: invoice.invoice_id,
        amount: paymentAmount,
        payment_method: paymentMethod || undefined,
        notes: notes || undefined,
      });
      
      // Create mock payment object for receipt (in real app, this would come from API)
      const payment: Payment = {
        payment_id: `PAY-${Date.now()}`,
        invoice_id: invoice.invoice_id,
        amount: paymentAmount,
        payment_date: new Date().toISOString(),
        payment_method: paymentMethod || undefined,
        notes: notes || undefined,
        created_at: new Date().toISOString(),
      };
      
      setLastPayment(payment);
      setShowReceipt(true);
      
      // Reset form
      setAmount('');
      setPaymentMethod('');
      setNotes('');
      onClose();
      
      toast.success('Payment processed successfully!');
    } catch (error) {
      toast.error('Failed to process payment. Please try again.');
    }
  };

  const handleClose = () => {
    setAmount('');
    setPaymentMethod('');
    setNotes('');
    onClose();
  };

  const handleReceiptClose = () => {
    setShowReceipt(false);
    setLastPayment(null);
  };

  const paymentAmount = parseFloat(amount) || 0;
  const isFullPayment = paymentAmount === invoice.remaining_balance;

  return (
    <>
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Process Payment</DialogTitle>
      <DialogContent>
        <Box mb={2}>
          <Typography variant="subtitle1" gutterBottom>
            Invoice: {invoice.invoice_number}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Remaining Balance: <AmountDisplay amount={invoice.remaining_balance} />
          </Typography>
        </Box>

        {isFullPayment && paymentAmount > 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            This will be a full payment and the invoice status will change to PAID.
          </Alert>
        )}

        <Box display="flex" alignItems="center">
          <TextField
            fullWidth
            label="Payment Amount"
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            inputProps={{ 
              min: 0, 
              max: invoice.remaining_balance, 
              step: 0.01 
            }}
            sx={{ mb: 2 }}
            required
          />
          <HelpTooltip title="Enter the amount being paid. Cannot exceed the remaining balance." />
        </Box>

        <TextField
          select
          fullWidth
          label="Payment Method"
          value={paymentMethod}
          onChange={(e) => setPaymentMethod(e.target.value)}
          sx={{ mb: 2 }}
        >
          <MenuItem value="">Select Payment Method</MenuItem>
          <MenuItem value="CASH">Cash</MenuItem>
          <MenuItem value="CHECK">Check</MenuItem>
          <MenuItem value="CREDIT_CARD">Credit Card</MenuItem>
          <MenuItem value="BANK_TRANSFER">Bank Transfer</MenuItem>
          <MenuItem value="OTHER">Other</MenuItem>
        </TextField>

        <TextField
          fullWidth
          label="Notes (Optional)"
          multiline
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add any notes about this payment..."
        />

        {paymentAmount > 0 && (
          <Box mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
            <Typography variant="body2">
              <strong>Payment Summary:</strong>
            </Typography>
            <Typography variant="body2">
              Payment Amount: <AmountDisplay amount={paymentAmount} />
            </Typography>
            <Typography variant="body2">
              Remaining After Payment: <AmountDisplay amount={invoice.remaining_balance - paymentAmount} />
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained"
          disabled={!amount || processPayment.isPending}
        >
          {processPayment.isPending ? 'Processing...' : 'Process Payment'}
        </Button>
      </DialogActions>
    </Dialog>
    
    <PaymentReceipt
      open={showReceipt}
      onClose={handleReceiptClose}
      payment={lastPayment}
      invoiceNumber={invoice.invoice_number}
    />
    </>
  );
};

export default PaymentModal;