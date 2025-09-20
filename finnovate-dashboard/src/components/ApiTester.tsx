import React, { useState } from 'react';
import {
  Box, Paper, Typography, Button, TextField, Alert, Accordion,
  AccordionSummary, AccordionDetails, Chip, CircularProgress
} from '@mui/material';
import { ExpandMore, PlayArrow, CheckCircle, Error } from '@mui/icons-material';
import { apiService } from '../services/api';

interface TestResult {
  name: string;
  status: 'pending' | 'success' | 'error';
  message: string;
  duration?: number;
}

const ApiTester: React.FC = () => {
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const updateResult = (name: string, status: 'success' | 'error', message: string, duration?: number) => {
    setResults(prev => prev.map(result => 
      result.name === name ? { ...result, status, message, duration } : result
    ));
  };

  const runTests = async () => {
    setIsRunning(true);
    const testCases = [
      'Get All Invoices',
      'Create Invoice',
      'Get Single Invoice',
      'Update Invoice Status',
      'Process Payment',
      'Delete Invoice',
      'Get Customers',
      'Get Payment History'
    ];

    setResults(testCases.map(name => ({ name, status: 'pending', message: 'Running...' })));

    // Test 1: Get All Invoices
    try {
      const start = Date.now();
      const invoices = await apiService.getInvoices();
      updateResult('Get All Invoices', 'success', `Retrieved ${invoices.length} invoices`, Date.now() - start);
    } catch (error) {
      updateResult('Get All Invoices', 'error', (error as Error).message);
    }

    // Test 2: Create Invoice
    let createdInvoiceId = '';
    try {
      const start = Date.now();
      const testInvoice = {
        customer_id: 'TEST-001',
        customer_name: 'Test Customer',
        customer_email: 'test@example.com',
        due_date: '2024-12-31',
        line_items: [{
          description: 'Test Service',
          quantity: 1,
          unit_price: 100.00
        }]
      };
      const invoice = await apiService.createInvoice(testInvoice);
      createdInvoiceId = invoice.invoice_id;
      updateResult('Create Invoice', 'success', `Created invoice ${invoice.invoice_number}`, Date.now() - start);
    } catch (error) {
      updateResult('Create Invoice', 'error', (error as Error).message);
    }

    // Test 3: Get Single Invoice
    if (createdInvoiceId) {
      try {
        const start = Date.now();
        const invoice = await apiService.getInvoice(createdInvoiceId);
        updateResult('Get Single Invoice', 'success', `Retrieved invoice ${invoice.invoice_number}`, Date.now() - start);
      } catch (error) {
        updateResult('Get Single Invoice', 'error', (error as Error).message);
      }
    } else {
      updateResult('Get Single Invoice', 'error', 'Skipped - no invoice created');
    }

    // Test 4: Update Invoice Status
    if (createdInvoiceId) {
      try {
        const start = Date.now();
        await apiService.updateInvoiceStatus(createdInvoiceId, 'SENT');
        updateResult('Update Invoice Status', 'success', 'Status updated to SENT', Date.now() - start);
      } catch (error) {
        updateResult('Update Invoice Status', 'error', (error as Error).message);
      }
    } else {
      updateResult('Update Invoice Status', 'error', 'Skipped - no invoice created');
    }

    // Test 5: Process Payment
    if (createdInvoiceId) {
      try {
        const start = Date.now();
        await apiService.processPayment({
          invoice_id: createdInvoiceId,
          amount: 50.00,
          payment_method: 'TEST'
        });
        updateResult('Process Payment', 'success', 'Payment of RM 50.00 processed', Date.now() - start);
      } catch (error) {
        updateResult('Process Payment', 'error', (error as Error).message);
      }
    } else {
      updateResult('Process Payment', 'error', 'Skipped - no invoice created');
    }

    // Test 6: Get Customers
    try {
      const start = Date.now();
      const customers = await apiService.getCustomers();
      updateResult('Get Customers', 'success', `Retrieved ${customers.length} customers`, Date.now() - start);
    } catch (error) {
      updateResult('Get Customers', 'error', (error as Error).message);
    }

    // Test 7: Get Payment History
    if (createdInvoiceId) {
      try {
        const start = Date.now();
        const history = await apiService.getPaymentHistory(createdInvoiceId);
        updateResult('Get Payment History', 'success', `Retrieved ${history.payments.length} payments`, Date.now() - start);
      } catch (error) {
        updateResult('Get Payment History', 'error', (error as Error).message);
      }
    } else {
      updateResult('Get Payment History', 'error', 'Skipped - no invoice created');
    }

    // Test 8: Delete Invoice (cleanup)
    if (createdInvoiceId) {
      try {
        const start = Date.now();
        await apiService.deleteInvoice(createdInvoiceId);
        updateResult('Delete Invoice', 'success', 'Test invoice deleted', Date.now() - start);
      } catch (error) {
        updateResult('Delete Invoice', 'error', (error as Error).message);
      }
    } else {
      updateResult('Delete Invoice', 'error', 'Skipped - no invoice created');
    }

    setIsRunning(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle color="success" />;
      case 'error': return <Error color="error" />;
      default: return <CircularProgress size={20} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const successCount = results.filter(r => r.status === 'success').length;
  const errorCount = results.filter(r => r.status === 'error').length;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        API Integration Tester
      </Typography>
      
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Button
          variant="contained"
          startIcon={<PlayArrow />}
          onClick={runTests}
          disabled={isRunning}
        >
          {isRunning ? 'Running Tests...' : 'Run All Tests'}
        </Button>
        
        {results.length > 0 && (
          <Box display="flex" gap={1}>
            <Chip label={`${successCount} Passed`} color="success" size="small" />
            <Chip label={`${errorCount} Failed`} color="error" size="small" />
          </Box>
        )}
      </Box>

      {results.length > 0 && (
        <Alert severity={errorCount === 0 ? 'success' : 'warning'} sx={{ mb: 2 }}>
          {errorCount === 0 
            ? 'All tests passed! API integration is working correctly.'
            : `${errorCount} test(s) failed. Check the details below.`
          }
        </Alert>
      )}

      {results.map((result, index) => (
        <Accordion key={index}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box display="flex" alignItems="center" gap={2} width="100%">
              {getStatusIcon(result.status)}
              <Typography>{result.name}</Typography>
              <Box flexGrow={1} />
              <Chip 
                label={result.status} 
                color={getStatusColor(result.status) as any} 
                size="small" 
              />
              {result.duration && (
                <Typography variant="caption" color="textSecondary">
                  {result.duration}ms
                </Typography>
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="textSecondary">
              {result.message}
            </Typography>
          </AccordionDetails>
        </Accordion>
      ))}
    </Paper>
  );
};

export default ApiTester;