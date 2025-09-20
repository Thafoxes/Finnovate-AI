import { useMemo } from 'react';
import { Invoice, Customer } from '../types';

export const useOptimizedInvoiceData = (invoices: Invoice[]) => {
  return useMemo(() => {
    const stats = {
      total: invoices.length,
      draft: invoices.filter(inv => inv.status === 'DRAFT').length,
      sent: invoices.filter(inv => inv.status === 'SENT').length,
      paid: invoices.filter(inv => inv.status === 'PAID').length,
      overdue: invoices.filter(inv => inv.status === 'OVERDUE').length,
      totalAmount: invoices.reduce((sum, inv) => sum + inv.total_amount, 0),
      paidAmount: invoices.reduce((sum, inv) => sum + inv.paid_amount, 0),
      outstandingAmount: invoices.reduce((sum, inv) => sum + inv.remaining_balance, 0),
    };

    const overdueInvoices = invoices.filter(inv => {
      const now = new Date();
      const dueDate = new Date(inv.due_date);
      return dueDate < now && inv.remaining_balance > 0;
    });

    return { stats, overdueInvoices };
  }, [invoices]);
};

export const useOptimizedCustomerData = (customers: Customer[]) => {
  return useMemo(() => {
    const stats = {
      total: customers.length,
      active: customers.filter(c => c.outstanding_amount > 0).length,
      highRisk: customers.filter(c => 
        c.total_amount > 0 && (c.outstanding_amount / c.total_amount) > 0.7
      ).length,
      totalOutstanding: customers.reduce((sum, c) => sum + c.outstanding_amount, 0),
    };

    return { stats };
  }, [customers]);
};