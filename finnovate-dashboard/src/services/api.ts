import { Invoice, Customer, CreateInvoiceForm, UpdateInvoiceForm, PaymentForm, PaymentHistory, ApiResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

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
    const response = await this.request<any>('/invoices');
    // Handle different response formats
    if (response.data && Array.isArray(response.data)) {
      return response.data;
    }
    if (Array.isArray(response)) {
      return response;
    }
    console.error('Unexpected response format:', response);
    return [];
  }

  async getInvoice(invoiceId: string): Promise<Invoice> {
    const response = await this.request<any>(`/invoices?invoice_id=${invoiceId}`);
    // Handle different response formats
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
    await this.request(`/invoices/${invoiceId}`, {
      method: 'DELETE',
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

  // Customer operations
  async getCustomers(): Promise<Customer[]> {
    // Generate customers from invoices since /customers endpoint doesn't exist yet
    try {
      const invoices = await this.getInvoices();
      const customerMap = new Map<string, Customer>();
      
      invoices.forEach(invoice => {
        const customerId = invoice.customer_id;
        if (!customerMap.has(customerId)) {
          customerMap.set(customerId, {
            customer_id: customerId,
            customer_name: invoice.customer_name,
            customer_email: invoice.customer_email,
            total_invoices: 0,
            total_amount: 0,
            paid_amount: 0,
            outstanding_amount: 0,
          });
        }
        
        const customer = customerMap.get(customerId)!;
        customer.total_invoices++;
        customer.total_amount += invoice.total_amount;
        customer.paid_amount += invoice.paid_amount;
        customer.outstanding_amount += invoice.remaining_balance;
      });
      
      return Array.from(customerMap.values());
    } catch (error) {
      console.error('Error generating customers from invoices:', error);
      return [];
    }
  }

  async getCustomer(customerId: string): Promise<Customer> {
    const customers = await this.getCustomers();
    const customer = customers.find(c => c.customer_id === customerId);
    if (!customer) {
      throw new Error('Customer not found');
    }
    return customer;
  }

  async getCustomerInvoices(customerId: string): Promise<Invoice[]> {
    const invoices = await this.getInvoices();
    return invoices.filter(invoice => invoice.customer_id === customerId);
  }

  // Overdue check
  async checkOverdueInvoices(): Promise<void> {
    await this.request('/overdue-check', {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();