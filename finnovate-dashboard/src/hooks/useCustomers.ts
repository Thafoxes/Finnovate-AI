import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { Customer, Invoice } from '../types';

export const useCustomers = () => {
  return useQuery<Customer[]>({
    queryKey: ['customers'],
    queryFn: () => apiService.getCustomers(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchInterval: false,
    retry: 1,
  });
};

export const useCustomer = (customerId: string) => {
  return useQuery<Customer>({
    queryKey: ['customer', customerId],
    queryFn: () => apiService.getCustomer(customerId),
    enabled: !!customerId,
  });
};

export const useCustomerInvoices = (customerId: string) => {
  return useQuery<Invoice[]>({
    queryKey: ['customer-invoices', customerId],
    queryFn: () => apiService.getCustomerInvoices(customerId),
    enabled: !!customerId,
  });
};