import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, TextField, Button, IconButton, Grid,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import { Add, Delete, Save, Cancel } from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useInvoice, useUpdateInvoice } from '../hooks/useInvoices';
import { UpdateInvoiceForm, InvoiceLineItem } from '../types';
import AmountDisplay from '../components/AmountDisplay';

const EditInvoice: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: invoice, isLoading } = useInvoice(id!);
  const updateInvoice = useUpdateInvoice();

  const [formData, setFormData] = useState<UpdateInvoiceForm>({
    customer_name: '',
    customer_email: '',
    due_date: '',
    line_items: [{ description: '', quantity: 1, unit_price: 0 }],
  });

  useEffect(() => {
    if (invoice) {
      setFormData({
        customer_name: invoice.customer_name,
        customer_email: invoice.customer_email,
        due_date: invoice.due_date,
        line_items: invoice.line_items.map(item => ({
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
      });
    }
  }, [invoice]);

  const addLineItem = () => {
    setFormData(prev => ({
      ...prev,
      line_items: [...prev.line_items, { description: '', quantity: 1, unit_price: 0 }]
    }));
  };

  const removeLineItem = (index: number) => {
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index)
    }));
  };

  const updateLineItem = (index: number, field: keyof Omit<InvoiceLineItem, 'total'>, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const calculateTotal = () => {
    return formData.line_items.reduce((total, item) => 
      total + (item.quantity * item.unit_price), 0
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.customer_name || !formData.customer_email || !formData.due_date) {
      alert('Please fill in all required fields');
      return;
    }

    if (formData.line_items.some(item => !item.description || item.quantity <= 0 || item.unit_price <= 0)) {
      alert('Please complete all line items');
      return;
    }

    try {
      await updateInvoice.mutateAsync({
        invoiceId: id!,
        data: formData,
      });
      navigate(`/invoices/${id}`);
    } catch (error) {
      alert('Failed to update invoice');
    }
  };

  if (isLoading) return <Typography>Loading invoice...</Typography>;
  if (!invoice) return <Typography color="error">Invoice not found</Typography>;
  if (invoice.status !== 'DRAFT') {
    return (
      <Box>
        <Typography color="error">Only DRAFT invoices can be edited</Typography>
        <Button onClick={() => navigate(`/invoices/${id}`)}>Back to Invoice</Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Edit Invoice</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Cancel />}
            onClick={() => navigate(`/invoices/${id}`)}
            sx={{ mr: 2 }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSubmit}
            disabled={updateInvoice.isPending}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Customer Name"
                required
                value={formData.customer_name}
                onChange={(e) => setFormData(prev => ({ ...prev, customer_name: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Customer Email"
                type="email"
                required
                value={formData.customer_email}
                onChange={(e) => setFormData(prev => ({ ...prev, customer_email: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Due Date"
                type="date"
                required
                InputLabelProps={{ shrink: true }}
                value={formData.due_date}
                onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
              />
            </Grid>
          </Grid>

          <Box mt={4}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Line Items</Typography>
              <Button startIcon={<Add />} onClick={addLineItem}>
                Add Item
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Description</TableCell>
                    <TableCell width="120px">Quantity</TableCell>
                    <TableCell width="150px">Unit Price</TableCell>
                    <TableCell width="150px">Total</TableCell>
                    <TableCell width="80px">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {formData.line_items.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <TextField
                          fullWidth
                          placeholder="Item description"
                          value={item.description}
                          onChange={(e) => updateLineItem(index, 'description', e.target.value)}
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          type="number"
                          value={item.quantity}
                          onChange={(e) => updateLineItem(index, 'quantity', parseInt(e.target.value) || 0)}
                          inputProps={{ min: 1 }}
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          type="number"
                          value={item.unit_price}
                          onChange={(e) => updateLineItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                          inputProps={{ min: 0, step: 0.01 }}
                        />
                      </TableCell>
                      <TableCell>
                        <AmountDisplay amount={item.quantity * item.unit_price} />
                      </TableCell>
                      <TableCell>
                        {formData.line_items.length > 1 && (
                          <IconButton onClick={() => removeLineItem(index)} color="error">
                            <Delete />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Box display="flex" justifyContent="flex-end" mt={2}>
              <Typography variant="h6">
                Total: <AmountDisplay amount={calculateTotal()} variant="h6" />
              </Typography>
            </Box>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default EditInvoice;