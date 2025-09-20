import React, { useState } from 'react';
import {
  Box, IconButton, Badge, Popover, List, ListItem, ListItemText,
  Typography, Divider, Button, Chip
} from '@mui/material';
import { Notifications, Warning, Info, CheckCircle } from '@mui/icons-material';
import { useInvoices } from '../hooks/useInvoices';
import { useCustomers } from '../hooks/useCustomers';

const NotificationCenter: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const { data: invoices = [] } = useInvoices();
  const { data: customers = [] } = useCustomers();

  const generateNotifications = () => {
    const notifications = [];
    const now = new Date();

    // Overdue invoices
    const overdueInvoices = invoices.filter(inv => {
      const dueDate = new Date(inv.due_date);
      return dueDate < now && inv.remaining_balance > 0;
    });

    if (overdueInvoices.length > 0) {
      notifications.push({
        id: 'overdue',
        type: 'warning',
        title: `${overdueInvoices.length} Overdue Invoices`,
        message: 'Require immediate attention',
        time: 'Now',
        action: 'View Overdue'
      });
    }

    // Due soon (next 7 days)
    const dueSoonInvoices = invoices.filter(inv => {
      const dueDate = new Date(inv.due_date);
      const sevenDaysFromNow = new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000));
      return dueDate >= now && dueDate <= sevenDaysFromNow && inv.remaining_balance > 0;
    });

    if (dueSoonInvoices.length > 0) {
      notifications.push({
        id: 'due-soon',
        type: 'info',
        title: `${dueSoonInvoices.length} Invoices Due Soon`,
        message: 'Due within the next 7 days',
        time: 'Today',
        action: 'Review'
      });
    }

    // High-risk customers
    const highRiskCustomers = customers.filter(customer => {
      const outstandingRatio = customer.total_amount > 0 ? 
        customer.outstanding_amount / customer.total_amount : 0;
      return outstandingRatio > 0.7;
    });

    if (highRiskCustomers.length > 0) {
      notifications.push({
        id: 'high-risk',
        type: 'warning',
        title: `${highRiskCustomers.length} High-Risk Customers`,
        message: 'Outstanding ratio > 70%',
        time: '2 hours ago',
        action: 'View Customers'
      });
    }

    // Recent payments
    const recentPayments = invoices.filter(inv => 
      inv.paid_amount > 0 && inv.status === 'PAID'
    ).slice(0, 3);

    recentPayments.forEach((invoice, index) => {
      notifications.push({
        id: `payment-${invoice.invoice_id}`,
        type: 'success',
        title: 'Payment Received',
        message: `${invoice.customer_name} - ${invoice.invoice_number}`,
        time: `${index + 1} hour${index > 0 ? 's' : ''} ago`,
        action: 'View Invoice'
      });
    });

    return notifications;
  };

  const notifications = generateNotifications();
  const unreadCount = notifications.length;

  const getIcon = (type: string) => {
    switch (type) {
      case 'warning': return <Warning color="warning" />;
      case 'success': return <CheckCircle color="success" />;
      default: return <Info color="info" />;
    }
  };

  const getChipColor = (type: string) => {
    switch (type) {
      case 'warning': return 'warning';
      case 'success': return 'success';
      default: return 'info';
    }
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  return (
    <>
      <IconButton color="inherit" onClick={handleClick}>
        <Badge badgeContent={unreadCount} color="error">
          <Notifications />
        </Badge>
      </IconButton>
      
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <Box sx={{ width: 350, maxHeight: 400 }}>
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h6">Notifications</Typography>
          </Box>
          
          {notifications.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="textSecondary">
                No new notifications
              </Typography>
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {notifications.map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <ListItem sx={{ alignItems: 'flex-start' }}>
                    <Box sx={{ mr: 2, mt: 0.5 }}>
                      {getIcon(notification.type)}
                    </Box>
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="subtitle2">
                            {notification.title}
                          </Typography>
                          <Chip 
                            label={notification.action} 
                            size="small" 
                            color={getChipColor(notification.type) as any}
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            {notification.message}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {notification.time}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < notifications.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
          
          {notifications.length > 0 && (
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Button fullWidth variant="text" size="small">
                Mark All as Read
              </Button>
            </Box>
          )}
        </Box>
      </Popover>
    </>
  );
};

export default NotificationCenter;