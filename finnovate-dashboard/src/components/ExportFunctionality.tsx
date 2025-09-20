import React, { useState } from 'react';
import {
  Button, Menu, MenuItem, ListItemIcon, ListItemText
} from '@mui/material';
import { FileDownload, PictureAsPdf, TableChart, Description } from '@mui/icons-material';
import { Invoice } from '../types';

interface ExportFunctionalityProps {
  data: Invoice[];
  filename?: string;
}

const ExportFunctionality: React.FC<ExportFunctionalityProps> = ({ 
  data, 
  filename = 'invoices' 
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const exportToCSV = () => {
    const headers = [
      'Invoice Number',
      'Customer Name',
      'Customer Email',
      'Status',
      'Issue Date',
      'Due Date',
      'Total Amount',
      'Paid Amount',
      'Remaining Balance'
    ];

    const csvContent = [
      headers.join(','),
      ...data.map(invoice => [
        invoice.invoice_number,
        `"${invoice.customer_name}"`,
        invoice.customer_email,
        invoice.status,
        invoice.issue_date,
        invoice.due_date,
        invoice.total_amount,
        invoice.paid_amount,
        invoice.remaining_balance
      ].join(','))
    ].join('\n');

    downloadFile(csvContent, `${filename}.csv`, 'text/csv');
    handleClose();
  };

  const exportToJSON = () => {
    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, `${filename}.json`, 'application/json');
    handleClose();
  };

  const exportToPDF = () => {
    // In a real app, this would generate a proper PDF
    const htmlContent = generateHTMLReport();
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.html`;
    link.click();
    URL.revokeObjectURL(url);
    handleClose();
  };

  const generateHTMLReport = () => {
    const totalAmount = data.reduce((sum, inv) => sum + inv.total_amount, 0);
    const paidAmount = data.reduce((sum, inv) => sum + inv.paid_amount, 0);
    const outstandingAmount = totalAmount - paidAmount;

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Invoice Report</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          .header { text-align: center; margin-bottom: 30px; }
          .summary { background: #f5f5f5; padding: 15px; margin-bottom: 20px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
          .amount { text-align: right; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>Invoice Report</h1>
          <p>Generated on ${new Date().toLocaleDateString()}</p>
        </div>
        
        <div class="summary">
          <h3>Summary</h3>
          <p>Total Invoices: ${data.length}</p>
          <p>Total Amount: RM ${totalAmount.toFixed(2)}</p>
          <p>Paid Amount: RM ${paidAmount.toFixed(2)}</p>
          <p>Outstanding: RM ${outstandingAmount.toFixed(2)}</p>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Customer</th>
              <th>Status</th>
              <th>Issue Date</th>
              <th>Due Date</th>
              <th class="amount">Total</th>
              <th class="amount">Paid</th>
              <th class="amount">Balance</th>
            </tr>
          </thead>
          <tbody>
            ${data.map(invoice => `
              <tr>
                <td>${invoice.invoice_number}</td>
                <td>${invoice.customer_name}</td>
                <td>${invoice.status}</td>
                <td>${new Date(invoice.issue_date).toLocaleDateString()}</td>
                <td>${new Date(invoice.due_date).toLocaleDateString()}</td>
                <td class="amount">RM ${invoice.total_amount.toFixed(2)}</td>
                <td class="amount">RM ${invoice.paid_amount.toFixed(2)}</td>
                <td class="amount">RM ${invoice.remaining_balance.toFixed(2)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </body>
      </html>
    `;
  };

  const downloadFile = (content: string, fileName: string, contentType: string) => {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <Button
        variant="outlined"
        startIcon={<FileDownload />}
        onClick={handleClick}
        disabled={data.length === 0}
      >
        Export
      </Button>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
      >
        <MenuItem onClick={exportToCSV}>
          <ListItemIcon>
            <TableChart />
          </ListItemIcon>
          <ListItemText>Export as CSV</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={exportToPDF}>
          <ListItemIcon>
            <PictureAsPdf />
          </ListItemIcon>
          <ListItemText>Export as PDF Report</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={exportToJSON}>
          <ListItemIcon>
            <Description />
          </ListItemIcon>
          <ListItemText>Export as JSON</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
};

export default ExportFunctionality;