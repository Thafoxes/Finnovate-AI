import { Invoice, Customer, CreateInvoiceForm, UpdateInvoiceForm, PaymentForm, PaymentHistory, ApiResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://h3330zxmg8.execute-api.us-east-1.amazonaws.com/prod';

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}, retries = 3): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Only add Content-Type for requests with body (POST, PUT, PATCH)
    const hasBody = options.method && ['POST', 'PUT', 'PATCH'].includes(options.method.toUpperCase());
    
    const config: RequestInit = {
      headers: {
        ...(hasBody && { 'Content-Type': 'application/json' }), // Only add for requests with body
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
      
      console.log('Raw API Response:', response);
      
      // Handle your Lambda's response format - be more defensive
      let invoicesData = [];
      
      if (response.success && response.data) {
        // Check for the new format with summary and invoices
        if (response.data.invoices && Array.isArray(response.data.invoices)) {
          invoicesData = response.data.invoices;
        } else if (Array.isArray(response.data)) {
          invoicesData = response.data;
        } else if (typeof response.data === 'object') {
          // If data is an object, extract array properties
          const possibleArrays = Object.values(response.data).filter(Array.isArray);
          if (possibleArrays.length > 0) {
            invoicesData = possibleArrays[0] as any[];
          } else {
            // No arrays found, create empty array and log the structure
            console.log('No invoice arrays found in response.data:', response.data);
            invoicesData = [];
          }
        }
      } else if (Array.isArray(response)) {
        invoicesData = response;
      } else if (response.invoices && Array.isArray(response.invoices)) {
        invoicesData = response.invoices;
      } else {
        console.log('Unexpected response format:', response);
        invoicesData = [];
      }
      
      return this.formatInvoicesResponse(invoicesData);
    } catch (error) {
      console.error('Error in getInvoices:', error);
      // Return empty array instead of crashing
      return [];
    }
  }

  private formatInvoicesResponse(invoices: any[]): Invoice[] {
    return invoices.map((invoice: any) => ({
      ...invoice,
      paid_amount: invoice.status === 'PAID' ? invoice.amount || invoice.total_amount || 0 : 0,
      remaining_balance: invoice.status === 'PAID' ? 0 : (invoice.amount || invoice.total_amount || 0),
      total_amount: invoice.amount || invoice.total_amount || 0
    }));
  }

  async getInvoice(invoiceId: string): Promise<Invoice> {
    // Validate invoice ID
    if (!invoiceId || invoiceId.trim().length === 0) {
      throw new Error('Invoice ID is required');
    }
    
    const cleanId = invoiceId.trim();
    if (cleanId.length < 3) {
      throw new Error('Invalid invoice ID format');
    }
    
    console.log(`Fetching invoice: ${cleanId}`);
    const response = await this.request<any>(`/invoices?invoice_id=${cleanId}`);
    
    // Handle your Lambda's response format
    if (response.success && response.data) {
      return this.formatSingleInvoice(response.data);
    } else if (response.data) {
      return this.formatSingleInvoice(response.data);
    } else if (response.invoice_id) {
      return this.formatSingleInvoice(response);
    }
    throw new Error('Invoice not found');
  }

  private formatSingleInvoice(invoice: any): Invoice {
    return {
      ...invoice,
      subtotal: invoice.amount || invoice.total_amount || 0,
      paid_amount: invoice.paid_amount || 0,
      remaining_balance: (invoice.amount || invoice.total_amount || 0) - (invoice.paid_amount || 0),
      total_amount: invoice.amount || invoice.total_amount || 0,
      line_items: invoice.items || invoice.line_items || []
    };
  }

  async createInvoice(invoiceData: CreateInvoiceForm): Promise<Invoice> {
    const response = await this.request<any>('/invoices', {
      method: 'POST',
      body: JSON.stringify(invoiceData),
    });
    
    if (response.success && response.data) {
      return response.data;
    } else if (response.data) {
      return response.data;
    } else if (response.invoice_id) {
      return response;
    }
    throw new Error('Failed to create invoice');
  }

  async updateInvoice(invoiceId: string, invoiceData: UpdateInvoiceForm): Promise<Invoice> {
    const response = await this.request<any>(`/invoices/${invoiceId}`, {
      method: 'PUT',
      body: JSON.stringify(invoiceData),
    });
    return response.data || response;
  }

  async updateInvoiceStatus(invoiceId: string, status: string): Promise<Invoice> {
    const response = await this.request<any>(`/invoices`, {
      method: 'PUT',
      body: JSON.stringify({ invoice_id: invoiceId, status }),
    });
    return response.data || response;
  }

  async deleteInvoice(invoiceId: string): Promise<void> {
    await this.request('/invoices', {
      method: 'DELETE',
      body: JSON.stringify({ invoice_id: invoiceId }),
    });
  }

  async getDashboardSummary(): Promise<any> {
    try {
      const response = await this.request<any>('/invoices');
      
      console.log('Dashboard Summary Response:', response);
      
      // Extract summary data from the response
      if (response.success && response.data && response.data.summary) {
        return response.data.summary;
      } else if (response.success && response.data) {
        // If the response.data already contains summary fields
        const data = response.data;
        if (data.total_invoices !== undefined) {
          return data;
        }
      }
      
      // Fallback to default summary
      return {
        total_invoices: 0,
        total_amount: 0,
        paid_invoices: 0,
        paid_amount: 0,
        overdue_invoices: 0,
        overdue_amount: 0,
        pending_invoices: 0,
        pending_amount: 0,
        average_invoice_amount: 0
      };
    } catch (error) {
      console.error('Error getting dashboard summary:', error);
      return {
        total_invoices: 0,
        total_amount: 0,
        paid_invoices: 0,
        paid_amount: 0,
        overdue_invoices: 0,
        overdue_amount: 0,
        pending_invoices: 0,
        pending_amount: 0,
        average_invoice_amount: 0
      };
    }
  }

  // Payment operations
  async processPayment(paymentData: PaymentForm): Promise<void> {
    await this.request('/payments', {
      method: 'POST',
      body: JSON.stringify(paymentData),
    });
  }

  async getPaymentHistory(invoiceId: string): Promise<PaymentHistory> {
    try {
      const invoice = await this.getInvoice(invoiceId);
      return {
        payments: [
          {
            payment_id: `PAY-${Date.now()}`,
            invoice_id: invoiceId,
            amount: invoice.paid_amount || 0,
            payment_date: invoice.updated_at || new Date().toISOString(),
            payment_method: 'BANK_TRANSFER',
            notes: 'Payment processed',
            created_at: invoice.updated_at || new Date().toISOString(),
          }
        ].filter(p => p.amount > 0),
        total_paid: invoice.paid_amount || 0,
        remaining_balance: invoice.remaining_balance || 0,
      };
    } catch (error) {
      return {
        payments: [],
        total_paid: 0,
        remaining_balance: 0,
      };
    }
  }

  // Customer operations
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
      
      let customers = [];
      if (response.success && response.data && response.data.customers) {
        customers = response.data.customers;
      } else if (response.success && Array.isArray(response.data)) {
        customers = response.data;
      } else if (Array.isArray(response)) {
        customers = response;
      } else {
        console.error('Unexpected customers response format:', response);
        return [];
      }
      
      return customers.map((customer: any) => ({
        ...customer,
        outstanding_amount: customer.overdue_amount || 0
      }));
    } catch (error) {
      console.error('Error fetching customers from API:', error);
      return [];
    }
  }

  async getCustomer(customerId: string): Promise<Customer> {
    const response = await this.request<any>(`/customers/${customerId}`);
    
    let customer;
    if (response.success && response.data) {
      customer = response.data;
    } else if (response.success && response.customer) {
      customer = response.customer;
    } else if (response.customer_id) {
      customer = response;
    } else {
      throw new Error('Customer not found');
    }
    
    return {
      ...customer,
      outstanding_amount: customer.overdue_amount || 0
    };
  }

  async getCustomerInvoices(customerId: string): Promise<Invoice[]> {
    const response = await this.request<any>(`/invoices?customer_id=${customerId}`);
    
    if (response.success && response.data && Array.isArray(response.data)) {
      return this.formatInvoicesResponse(response.data);
    } else if (response.success && response.invoices) {
      return this.formatInvoicesResponse(response.invoices);
    } else if (Array.isArray(response)) {
      return this.formatInvoicesResponse(response);
    }
    console.error('Unexpected customer invoices response format:', response);
    return [];
  }

  async getCustomerStatistics(): Promise<any> {
    const response = await this.request<any>('/customers/statistics');
    
    if (response.success && response.data) {
      return response.data;
    } else if (response.success && response.statistics) {
      return response.statistics;
    } else if (response.total_customers !== undefined) {
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

  async checkOverdueInvoices(): Promise<void> {
    await this.request('/overdue-check', {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();