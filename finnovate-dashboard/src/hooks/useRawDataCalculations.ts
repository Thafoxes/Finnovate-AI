import { useMemo } from 'react';
import { Invoice } from '../types';

export const useRawDataCalculations = (invoices: Invoice[]) => {
  return useMemo(() => {
    // Basic stats
    const basicStats = {
      total: invoices.length,
      draft: invoices.filter(inv => inv.status === 'DRAFT').length,
      sent: invoices.filter(inv => inv.status === 'SENT').length,
      paid: invoices.filter(inv => inv.status === 'PAID').length,
      overdue: invoices.filter(inv => inv.status === 'OVERDUE').length,
      totalAmount: invoices.reduce((sum, inv) => sum + (inv.total_amount || 0), 0),
      paidAmount: invoices.reduce((sum, inv) => {
        // Calculate paid amount based on status since paid_amount field might not exist
        if (inv.status === 'PAID') {
          return sum + (inv.total_amount || 0);
        }
        return sum + (inv.paid_amount || 0);
      }, 0),
      outstandingAmount: invoices.reduce((sum, inv) => {
        if (inv.status === 'PAID') {
          return sum;
        }
        return sum + (inv.remaining_balance || inv.total_amount || 0);
      }, 0),
    };

    // Cash flow by month
    const cashFlowData = invoices.reduce((acc, invoice) => {
      const dateStr = invoice.created_at || invoice.issue_date;
      if (!dateStr) return acc;
      
      try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return acc;
        
        const month = date.toISOString().slice(0, 7);
        if (!acc[month]) acc[month] = { invoiced: 0, paid: 0, outstanding: 0 };
        acc[month].invoiced += invoice.total_amount || 0;
        acc[month].paid += invoice.status === 'PAID' ? (invoice.total_amount || 0) : (invoice.paid_amount || 0);
        acc[month].outstanding += invoice.status === 'PAID' ? 0 : (invoice.remaining_balance || invoice.total_amount || 0);
      } catch (error) {
        console.warn('Invalid date in invoice:', dateStr);
      }
      return acc;
    }, {} as Record<string, { invoiced: number; paid: number; outstanding: number }>);

    // Customer segments
    const customerSegments = invoices.reduce((acc, invoice) => {
      const id = invoice.customer_id;
      if (!acc[id]) {
        acc[id] = {
          customer_id: id,
          customer_name: invoice.customer_name,
          totalAmount: 0,
          paidAmount: 0,
          invoiceCount: 0,
          overdueCount: 0
        };
      }
      acc[id].totalAmount += invoice.total_amount || 0;
      acc[id].paidAmount += invoice.status === 'PAID' ? (invoice.total_amount || 0) : (invoice.paid_amount || 0);
      acc[id].invoiceCount += 1;
      if (invoice.status === 'OVERDUE') acc[id].overdueCount += 1;
      return acc;
    }, {} as Record<string, any>);

    // Overdue analysis
    const overdueAnalysis = invoices
      .filter(inv => inv.status === 'OVERDUE')
      .reduce((acc, invoice) => {
        if (!invoice.due_date) return acc;
        
        try {
          const dueDate = new Date(invoice.due_date);
          if (isNaN(dueDate.getTime())) return acc;
          
          const daysPastDue = Math.floor(
            (Date.now() - dueDate.getTime()) / (1000 * 60 * 60 * 24)
          );
          const category = daysPastDue > 90 ? '90+ days' : 
                          daysPastDue > 60 ? '60-90 days' : 
                          daysPastDue > 30 ? '30-60 days' : '0-30 days';
          
          if (!acc[category]) acc[category] = { count: 0, amount: 0 };
          acc[category].count += 1;
          acc[category].amount += invoice.remaining_balance || 0;
        } catch (error) {
          console.warn('Invalid due_date in invoice:', invoice.due_date);
        }
        return acc;
      }, {} as Record<string, { count: number; amount: number }>);

    return {
      basicStats,
      cashFlowData: Object.entries(cashFlowData).map(([month, data]) => ({
        month,
        ...data,
        collectionRate: data.invoiced > 0 ? (data.paid / data.invoiced) * 100 : 0
      })),
      customerSegments: Object.values(customerSegments).map((customer: any) => ({
        ...customer,
        riskScore: customer.invoiceCount > 0 ? (customer.overdueCount / customer.invoiceCount) * 100 : 0
      })),
      overdueAnalysis: Object.entries(overdueAnalysis).map(([category, data]) => ({ category, ...data }))
    };
  }, [invoices]);
};