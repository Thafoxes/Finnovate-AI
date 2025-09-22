import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { CreateInvoiceForm, UpdateInvoiceForm, PaymentForm } from '../types';

export const useInvoices = () => {
  return useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiService.getInvoices(),
    staleTime: 60 * 60 * 1000, // 1 hour (as per requirement)
    gcTime: 2 * 60 * 60 * 1000, // 2 hours
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchInterval: 60 * 60 * 1000, // Auto-refresh every hour
    retry: 2,
  });
};

export const useDashboardSummary = () => {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => apiService.getDashboardSummary(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    retry: 2,
  });
};

export const useInvoice = (invoiceId: string) => {
  const queryClient = useQueryClient();
  
  // Clear any stale cache entries for invalid IDs
  React.useEffect(() => {
    if (!invoiceId || invoiceId.trim().length === 0) {
      queryClient.removeQueries({ queryKey: ['invoice'] });
    }
  }, [invoiceId, queryClient]);
  
  return useQuery({
    queryKey: ['invoice', invoiceId],
    queryFn: () => apiService.getInvoice(invoiceId),
    enabled: !!invoiceId && invoiceId.trim().length > 0,
    retry: 1, // Only retry once to prevent infinite loops
    staleTime: 5 * 60 * 1000, // 5 minutes
    // Add error boundary to prevent crashes
    throwOnError: false,
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