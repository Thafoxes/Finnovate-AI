import { Invoice, Customer, CreateInvoiceForm, UpdateInvoiceForm, PaymentForm, PaymentHistory, ApiResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Invoice operations
  async getInvoices(): Promise<Invoice[]> {
    const response = await this.request<ApiResponse<Invoice[]>>('/invoices');
    return response.data;
  }

  async getInvoice(invoiceId: string): Promise<Invoice> {
    const response = await this.request<ApiResponse<Invoice>>(`/invoices?invoice_id=${invoiceId}`);
    return response.data;
  }

  async createInvoice(invoiceData: CreateInvoiceForm): Promise<Invoice> {
    const response = await this.request<ApiResponse<Invoice>>('/invoices', {
      method: 'POST',
      body: JSON.stringify(invoiceData),
    });
    return response.data;
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
    const response = await this.request<ApiResponse<PaymentHistory>>(`/payments/${invoiceId}`);
    return response.data;
  }

  // Customer operations
  async getCustomers(): Promise<Customer[]> {
    const response = await this.request<ApiResponse<Customer[]>>('/customers');
    return response.data;
  }

  async getCustomer(customerId: string): Promise<Customer> {
    const response = await this.request<ApiResponse<Customer>>(`/customers/${customerId}`);
    return response.data;
  }

  async getCustomerInvoices(customerId: string): Promise<Invoice[]> {
    const response = await this.request<ApiResponse<Invoice[]>>(`/customers/${customerId}/invoices`);
    return response.data;
  }

  // Overdue check
  async checkOverdueInvoices(): Promise<void> {
    await this.request('/overdue-check', {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();