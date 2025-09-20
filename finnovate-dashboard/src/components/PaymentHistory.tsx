import React from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Chip
} from '@mui/material';
import { usePaymentHistory } from '../hooks/useInvoices';
import AmountDisplay from './AmountDisplay';

interface PaymentHistoryProps {
  invoiceId: string;
}

const PaymentHistory: React.FC<PaymentHistoryProps> = ({ invoiceId }) => {
  const { data: paymentHistory, isLoading, error } = usePaymentHistory(invoiceId);

  if (isLoading) return <Typography>Loading payment history...</Typography>;
  if (error) return <Typography color="error">Failed to load payment history</Typography>;
  if (!paymentHistory || paymentHistory.payments.length === 0) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>Payment History</Typography>
        <Typography color="textSecondary">No payments recorded for this invoice.</Typography>
      </Box>
    );
  }

  const getPaymentMethodColor = (method?: string) => {
    switch (method) {
      case 'CASH': return 'success';
      case 'CHECK': return 'warning';
      case 'CREDIT_CARD': return 'primary';
      case 'BANK_TRANSFER': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Payment History</Typography>
      
      <Box mb={2} p={2} bgcolor="grey.50" borderRadius={1}>
        <Typography variant="body2">
          <strong>Total Paid:</strong> <AmountDisplay amount={paymentHistory.total_paid} />
        </Typography>
        <Typography variant="body2">
          <strong>Remaining Balance:</strong> <AmountDisplay amount={paymentHistory.remaining_balance} />
        </Typography>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Method</TableCell>
              <TableCell>Notes</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paymentHistory.payments.map((payment) => (
              <TableRow key={payment.payment_id}>
                <TableCell>
                  {new Date(payment.payment_date).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <AmountDisplay amount={payment.amount} />
                </TableCell>
                <TableCell>
                  {payment.payment_method ? (
                    <Chip 
                      label={payment.payment_method.replace('_', ' ')} 
                      size="small"
                      color={getPaymentMethodColor(payment.payment_method) as any}
                    />
                  ) : (
                    <Typography variant="body2" color="textSecondary">-</Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {payment.notes || '-'}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default PaymentHistory;