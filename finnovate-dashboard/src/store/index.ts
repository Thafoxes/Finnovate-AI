import { configureStore } from '@reduxjs/toolkit';
import invoiceSlice from './slices/invoiceSlice';
import uiSlice from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    invoices: invoiceSlice,
    ui: uiSlice,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;