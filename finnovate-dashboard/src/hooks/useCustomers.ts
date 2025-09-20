import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';

export const useCustomers = () => {
  return useQuery({
    queryKey: ['customers'],
    queryFn: apiService.getCustomers,
  });
};

export const useCustomer = (customerId: string) => {
  return useQuery({
    queryKey: ['customer', customerId],
    queryFn: () => apiService.getCustomer(customerId),
    enabled: !!customerId,
  });
};

export const useCustomerInvoices = (customerId: string) => {
  return useQuery({
    queryKey: ['customer-invoices', customerId],
    queryFn: () => apiService.getCustomerInvoices(customerId),
    enabled: !!customerId,
  });
};