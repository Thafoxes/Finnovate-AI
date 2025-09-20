import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useSelector } from 'react-redux';
import { store, RootState } from './store';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import InvoiceList from './pages/InvoiceList';
import InvoiceDetails from './pages/InvoiceDetails';
import CreateInvoice from './pages/CreateInvoice';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppContent() {
  const theme = useSelector((state: RootState) => state.ui.theme);
  
  const muiTheme = createTheme({
    palette: {
      mode: theme,
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
    },
  });

  return (
    <ThemeProvider theme={muiTheme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/invoices" element={<InvoiceList />} />
            <Route path="/invoices/:id" element={<InvoiceDetails />} />
            <Route path="/invoices/create" element={<CreateInvoice />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <AppContent />
      </QueryClientProvider>
    </Provider>
  );
}

export default App;