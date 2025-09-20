// Invoice Types
export interface InvoiceLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface Invoice {
  invoice_id: string;
  invoice_number: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  line_items: InvoiceLineItem[];
  subtotal: number;
  total_amount: number;
  paid_amount: number;
  remaining_balance: number;
  created_at: string;
  updated_at: string;
}

export type InvoiceStatus = 'DRAFT' | 'SENT' | 'PAID' | 'OVERDUE';

// Payment Types
export interface Payment {
  payment_id: string;
  invoice_id: string;
  amount: number;
  payment_date: string;
  payment_method?: string;
  notes?: string;
  created_at: string;
}

export interface PaymentHistory {
  payments: Payment[];
  total_paid: number;
  remaining_balance: number;
}

// Customer Types
export interface Customer {
  customer_id: string;
  customer_name: string;
  customer_email: string;
  total_invoices: number;
  total_amount: number;
  paid_amount: number;
  overdue_amount: number;
  outstanding_amount: number; // Calculated from overdue_amount
  draft_count: number;
  sent_count: number;
  paid_count: number;
  overdue_count: number;
  last_invoice_date: string | null;
  risk_score: number;
  payment_ratio?: number;
  average_invoice_amount?: number;
  invoices?: Invoice[]; // For detailed customer view
}

export interface CustomerStatistics {
  total_customers: number;
  high_risk_customers: number;
  average_risk_score: number;
  total_customer_value: number;
  top_customers: {
    customer_id: string;
    customer_name: string;
    total_amount: number;
    risk_score: number;
  }[];
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

// Form Types
export interface CreateInvoiceForm {
  customer_id: string;
  customer_name: string;
  customer_email: string;
  due_date: string;
  line_items: Omit<InvoiceLineItem, 'total'>[];
}

export interface UpdateInvoiceForm {
  customer_name: string;
  customer_email: string;
  due_date: string;
  line_items: Omit<InvoiceLineItem, 'total'>[];
}

export interface PaymentForm {
  invoice_id: string;
  amount: number;
  payment_method?: string;
  notes?: string;
}

// Filter Types
export interface InvoiceFilters {
  status?: InvoiceStatus;
  customer_name?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

// Analytics Types
export interface CashFlowData {
  month: string;
  invoiced: number;
  collected: number;
  outstanding: number;
}

export interface PaymentTrendData {
  date: string;
  amount: number;
  count: number;
}

export interface CustomerSegmentData {
  segment: string;
  count: number;
  totalAmount: number;
  collectionRate: number;
}

export interface AnalyticsSummary {
  dso: number; // Days Sales Outstanding
  collectionEffectiveness: number;
  overdueRate: number;
  avgPaymentTime: number;
}