import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Invoice, InvoiceFilters } from '../../types';

interface InvoiceState {
  invoices: Invoice[];
  selectedInvoice: Invoice | null;
  filters: InvoiceFilters;
  loading: boolean;
  error: string | null;
}

const initialState: InvoiceState = {
  invoices: [],
  selectedInvoice: null,
  filters: {},
  loading: false,
  error: null,
};

const invoiceSlice = createSlice({
  name: 'invoices',
  initialState,
  reducers: {
    setInvoices: (state, action: PayloadAction<Invoice[]>) => {
      state.invoices = action.payload;
    },
    addInvoice: (state, action: PayloadAction<Invoice>) => {
      state.invoices.unshift(action.payload);
    },
    updateInvoice: (state, action: PayloadAction<Invoice>) => {
      const index = state.invoices.findIndex(inv => inv.invoice_id === action.payload.invoice_id);
      if (index !== -1) {
        state.invoices[index] = action.payload;
      }
    },
    deleteInvoice: (state, action: PayloadAction<string>) => {
      state.invoices = state.invoices.filter(inv => inv.invoice_id !== action.payload);
    },
    setSelectedInvoice: (state, action: PayloadAction<Invoice | null>) => {
      state.selectedInvoice = action.payload;
    },
    setFilters: (state, action: PayloadAction<InvoiceFilters>) => {
      state.filters = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  setInvoices,
  addInvoice,
  updateInvoice,
  deleteInvoice,
  setSelectedInvoice,
  setFilters,
  setLoading,
  setError,
} = invoiceSlice.actions;

export default invoiceSlice.reducer;