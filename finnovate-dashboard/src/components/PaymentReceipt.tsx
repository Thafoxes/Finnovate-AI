import React from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Typography, Box, Divider, Grid
} from '@mui/material';
import { CheckCircle } from '@mui/icons-material';
import AmountDisplay from './AmountDisplay';
import { Payment } from '../types';

interface PaymentReceiptProps {
  open: boolean;
  onClose: () => void;
  payment: Payment | null;
  invoiceNumber: string;
}

const PaymentReceipt: React.FC<PaymentReceiptProps> = ({ 
  open, 
  onClose, 
  payment, 
  invoiceNumber 
}) => {
  if (!payment) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <CheckCircle color="success" />
          <Typography variant="h6">Payment Confirmation</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box textAlign="center" mb={3}>
          <Typography variant="h4" color="success.main" gutterBottom>
            <AmountDisplay amount={payment.amount} variant="h6" />
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Payment processed successfully
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">
              Payment ID:
            </Typography>
            <Typography variant="body1">
              {payment.payment_id}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">
              Invoice:
            </Typography>
            <Typography variant="body1">
              {invoiceNumber}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">
              Payment Date:
            </Typography>
            <Typography variant="body1">
              {new Date(payment.payment_date).toLocaleDateString()}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">
              Payment Method:
            </Typography>
            <Typography variant="body1">
              {payment.payment_method?.replace('_', ' ') || 'Not specified'}
            </Typography>
          </Grid>
          {payment.notes && (
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary">
                Notes:
              </Typography>
              <Typography variant="body1">
                {payment.notes}
              </Typography>
            </Grid>
          )}
        </Grid>

        <Box mt={3} p={2} bgcolor="success.50" borderRadius={1}>
          <Typography variant="body2" color="success.dark">
            ✓ Payment has been recorded and applied to the invoice
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PaymentReceipt;