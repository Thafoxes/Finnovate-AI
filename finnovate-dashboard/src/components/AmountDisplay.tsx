import React from 'react';
import { Typography } from '@mui/material';

interface AmountDisplayProps {
  amount: number;
  currency?: string;
  variant?: 'body1' | 'body2' | 'h6' | 'subtitle1';
}

const AmountDisplay: React.FC<AmountDisplayProps> = ({ 
  amount, 
  currency = 'MYR', 
  variant = 'body1' 
}) => {
  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-MY', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  return (
    <Typography variant={variant} component="span">
      {formatAmount(amount, currency)}
    </Typography>
  );
};

export default AmountDisplay;