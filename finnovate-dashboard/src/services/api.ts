import { Invoice, Customer, CreateInvoiceForm, UpdateInvoiceForm, PaymentForm, PaymentHistory, ApiResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://59wn0kqhjl.execute-api.us-east-1.amazonaws.com/prod';

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}, retries = 3): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        console.log(`API Request: ${config.method || 'GET'} ${url}`);
        const response = await fetch(url, config);
        
        console.log(`API Response: ${response.status} ${response.statusText}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`API Error Details:`, { status: response.status, statusText: response.statusText, body: errorText });
          throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        const data = await response.json();
        console.log('API Response Data:', data);
        return data;
      } catch (error) {
        if (attempt === retries) {
          throw error;
        }
        
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
    
    throw new Error('Max retries exceeded');
  }

  // Invoice operations
  async getInvoices(): Promise<Invoice[]> {
    try {
      console.log('API_BASE_URL:', API_BASE_URL);
      const response = await this.request<any>('/invoices');
      let invoices = [];
      
      // Handle different response formats
      if (response.success && response.invoices) {
        invoices = response.invoices;
      } else if (response.data && Array.isArray(response.data)) {
        invoices = response.data;
      } else if (Array.isArray(response)) {
        invoices = response;
      } else {
        console.error('Unexpected response format:', response);
        return [];
      }
      
      // Add missing fields for frontend compatibility
      return invoices.map((invoice: any) => ({
        ...invoice,
        paid_amount: invoice.status === 'PAID' ? invoice.total_amount : 0,
        remaining_balance: invoice.status === 'PAID' ? 0 : invoice.total_amount
      }));
    } catch (error) {
      console.error('Error in getInvoices:', error);
      return [];
    }
  }

  async getInvoice(invoiceId: string): Promise<Invoice> {
    const response = await this.request<any>(`/invoices?invoice_id=${invoiceId}`);
    // Handle different response formats
    if (response.success && response.invoice) {
      const invoice = response.invoice;
      // Map line_total to total for frontend compatibility
      if (invoice.line_items) {
        invoice.line_items = invoice.line_items.map((item: any) => ({
          ...item,
          total: item.line_total || item.total
        }));
      }
      // Add missing fields for compatibility
      invoice.subtotal = invoice.total_amount;
      invoice.paid_amount = invoice.paid_amount || 0;
      invoice.remaining_balance = invoice.total_amount - (invoice.paid_amount || 0);
      return invoice;
    }
    if (response.data) {
      return response.data;
    }
    if (response.invoice_id) {
      return response;
    }
    throw new Error('Invoice not found');
  }

  async createInvoice(invoiceData: CreateInvoiceForm): Promise<Invoice> {
    const response = await this.request<any>('/invoices', {
      method: 'POST',
      body: JSON.stringify(invoiceData),
    });
    // Handle different response formats
    if (response.data) {
      return response.data;
    }
    if (response.invoice_id) {
      return response;
    }
    throw new Error('Failed to create invoice');
  }

  async updateInvoice(invoiceId: string, invoiceData: UpdateInvoiceForm): Promise<Invoice> {
    const response = await this.request<ApiResponse<Invoice>>(`/invoices/${invoiceId}`, {
      method: 'PUT',
      body: JSON.stringify(invoiceData),
    });
    return response.data;
  }

  async updateInvoiceStatus(invoiceId: string, status: string): Promise<Invoice> {
    const response = await this.request<ApiResponse<Invoice>>(`/invoices`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
      headers: {
        'invoice-id': invoiceId,
      },
    });
    return response.data;
  }

  async deleteInvoice(invoiceId: string): Promise<void> {
    await this.request('/invoices', {
      method: 'DELETE',
      body: JSON.stringify({ invoice_id: invoiceId }),
    });
  }

  // Payment operations
  async processPayment(paymentData: PaymentForm): Promise<void> {
    await this.request('/payments', {
      method: 'POST',
      body: JSON.stringify(paymentData),
    });
  }

  async getPaymentHistory(invoiceId: string): Promise<PaymentHistory> {
    // Mock payment history since endpoint might not exist yet
    const invoice = await this.getInvoice(invoiceId);
    return {
      payments: [
        {
          payment_id: `PAY-${Date.now()}`,
          invoice_id: invoiceId,
          amount: invoice.paid_amount,
          payment_date: invoice.updated_at,
          payment_method: 'BANK_TRANSFER',
          notes: 'Payment processed',
          created_at: invoice.updated_at,
        }
      ].filter(p => p.amount > 0),
      total_paid: invoice.paid_amount,
      remaining_balance: invoice.remaining_balance,
    };
  }

  // Customer operations - using real API endpoints
  async getCustomers(searchTerm?: string, riskFilter?: string, sortBy?: string, includeStats?: boolean): Promise<Customer[]> {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (riskFilter) params.append('risk_filter', riskFilter);
      if (sortBy) params.append('sort_by', sortBy);
      if (includeStats) params.append('include_stats', 'true');
      
      const queryString = params.toString();
      const endpoint = `/customers${queryString ? `?${queryString}` : ''}`;
      
      const response = await this.request<any>(endpoint);
      
      // Handle response format and add outstanding_amount for compatibility
      let customers = [];
      if (response.success && response.customers) {
        customers = response.customers;
      } else if (Array.isArray(response)) {
        customers = response;
      } else {
        console.error('Unexpected customers response format:', response);
        return [];
      }
      
      // Add outstanding_amount for backward compatibility
      return customers.map((customer: any) => ({
        ...customer,
        outstanding_amount: customer.overdue_amount || 0
      }));
    } catch (error) {
      console.error('Error fetching customers from API:', error);
      // Fallback to empty array instead of crashing
      return [];
    }
  }

  async getCustomer(customerId: string): Promise<Customer> {
    const response = await this.request<any>(`/customers/${customerId}`);
    
    // Handle response format and add outstanding_amount
    let customer;
    if (response.success && response.customer) {
      customer = response.customer;
    } else if (response.customer_id) {
      customer = response;
    } else {
      throw new Error('Customer not found');
    }
    
    // Add outstanding_amount for backward compatibility
    return {
      ...customer,
      outstanding_amount: customer.overdue_amount || 0
    };
  }

  async getCustomerInvoices(customerId: string): Promise<Invoice[]> {
    const response = await this.request<any>(`/customers/${customerId}/invoices`);
    
    // Handle response format
    if (response.success && response.invoices) {
      return response.invoices;
    }
    if (Array.isArray(response)) {
      return response;
    }
    console.error('Unexpected customer invoices response format:', response);
    return [];
  }

  async getCustomerStatistics(): Promise<any> {
    const response = await this.request<any>('/customers/statistics');
    
    // Handle response format
    if (response.success && response.statistics) {
      return response.statistics;
    }
    if (response.total_customers !== undefined) {
      return response;
    }
    console.error('Unexpected customer statistics response format:', response);
    return {
      total_customers: 0,
      high_risk_customers: 0,
      average_risk_score: 0,
      total_customer_value: 0,
      top_customers: []
    };
  }

  // Overdue check
  async checkOverdueInvoices(): Promise<void> {
    await this.request('/overdue-check', {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();