import React from 'react';
import { Chip } from '@mui/material';
import { InvoiceStatus } from '../types';

interface StatusBadgeProps {
  status: InvoiceStatus;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getStatusColor = (status: InvoiceStatus) => {
    switch (status) {
      case 'DRAFT': return 'default';
      case 'SENT': return 'primary';
      case 'PAID': return 'success';
      case 'OVERDUE': return 'error';
      default: return 'default';
    }
  };

  return (
    <Chip 
      label={status} 
      color={getStatusColor(status)} 
      size="small" 
      variant="filled"
    />
  );
};

export default StatusBadge;