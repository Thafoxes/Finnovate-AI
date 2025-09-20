import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { CreateInvoiceForm, UpdateInvoiceForm, PaymentForm } from '../types';

export const useInvoices = () => {
  return useQuery({
    queryKey: ['invoices'],
    queryFn: apiService.getInvoices,
  });
};

export const useInvoice = (invoiceId: string) => {
  return useQuery({
    queryKey: ['invoice', invoiceId],
    queryFn: () => apiService.getInvoice(invoiceId),
    enabled: !!invoiceId,
  });
};

export const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateInvoiceForm) => apiService.createInvoice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
};

export const useUpdateInvoiceStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ invoiceId, status }: { invoiceId: string; status: string }) =>
      apiService.updateInvoiceStatus(invoiceId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
};

export const useDeleteInvoice = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (invoiceId: string) => apiService.deleteInvoice(invoiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
};

export const useUpdateInvoice = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ invoiceId, data }: { invoiceId: string; data: UpdateInvoiceForm }) =>
      apiService.updateInvoice(invoiceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
};

export const usePaymentHistory = (invoiceId: string) => {
  return useQuery({
    queryKey: ['payments', invoiceId],
    queryFn: () => apiService.getPaymentHistory(invoiceId),
    enabled: !!invoiceId,
  });
};

export const useProcessPayment = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: PaymentForm) => apiService.processPayment(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['payments', variables.invoice_id] });
    },
  });
};