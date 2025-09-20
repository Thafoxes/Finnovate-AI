import { Invoice, CreateInvoiceForm, PaymentForm, ApiResponse } from '../types';

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

  // Overdue check
  async checkOverdueInvoices(): Promise<void> {
    await this.request('/overdue-check', {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();