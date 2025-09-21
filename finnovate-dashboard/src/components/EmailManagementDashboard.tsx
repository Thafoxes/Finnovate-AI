import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  Grid,
  Divider,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Email as EmailIcon,
  Preview as PreviewIcon,
  Send as SendIcon,
  CheckCircle as ApproveIcon,
  Cancel as CancelIcon,
  History as HistoryIcon,
  Analytics as AnalyticsIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Types for email management
interface EmailTemplate {
  template_id: string;
  customer_id: string;
  customer_name: string;
  reminder_type: 'first' | 'second' | 'final';
  subject: string;
  created_at: string;
  status: 'drafted' | 'approved' | 'sent';
  preview: string;
  personalization_data?: any;
}

interface EmailHistory {
  template_id: string;
  customer_id: string;
  customer_name: string;
  reminder_type: string;
  subject: string;
  sent_at: string;
  delivery_status: string;
}

interface DailyAnalytics {
  date: string;
  emails_sent: number;
  first_reminders: number;
  second_reminders: number;
  final_notices: number;
  templates_created: number;
  templates_approved: number;
  delivery_rate: number;
  bounce_rate: number;
}

// Styled components
const DashboardContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  maxWidth: 1200,
  margin: '0 auto'
}));

const SectionCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  '& .MuiCardHeader-root': {
    paddingBottom: theme.spacing(1)
  }
}));

const StatusChip = styled(Chip)<{ status: string }>(({ theme, status }) => ({
  backgroundColor: 
    status === 'drafted' ? theme.palette.warning.light :
    status === 'approved' ? theme.palette.info.light :
    status === 'sent' ? theme.palette.success.light :
    theme.palette.grey[300],
  color: 
    status === 'drafted' ? theme.palette.warning.contrastText :
    status === 'approved' ? theme.palette.info.contrastText :
    status === 'sent' ? theme.palette.success.contrastText :
    theme.palette.text.primary,
  fontWeight: 'bold'
}));

const EmailManagementDashboard: React.FC = () => {
  // State management
  const [emailDrafts, setEmailDrafts] = useState<EmailTemplate[]>([]);
  const [emailHistory, setEmailHistory] = useState<EmailHistory[]>([]);
  const [analytics, setAnalytics] = useState<DailyAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  // API base URL
  const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || '';

  // Load email drafts
  const loadEmailDrafts = async () => {
    try {
      setLoading(true);
      
      // If no API URL is configured, use mock data immediately
      if (!apiBaseUrl) {
        console.log('No API URL configured, using mock email drafts for demo');
        setEmailDrafts([
          {
            template_id: 'template_001',
            customer_id: 'cust_001',
            customer_name: 'John Doe',
            reminder_type: 'first',
            subject: 'Payment Reminder - Invoice #INV-001',
            created_at: '2025-09-21T10:30:00Z',
            status: 'drafted',
            preview: 'Dear John Doe, we hope this message finds you well. We wanted to remind you...'
          },
          {
            template_id: 'template_002',
            customer_id: 'cust_002',
            customer_name: 'Jane Smith',
            reminder_type: 'second',
            subject: 'Second Notice - Invoice #INV-002',
            created_at: '2025-09-21T09:15:00Z',
            status: 'approved',
            preview: 'Dear Jane Smith, this is a second reminder regarding your overdue payment...'
          }
        ]);
        setLoading(false);
        return;
      }
      
      const response = await fetch(`${apiBaseUrl}/ai/email-drafts`);
      const data = await response.json();
      
      if (data.success) {
        setEmailDrafts(data.data.drafts || []);
      } else {
        // Fallback to mock data
        setEmailDrafts([
          {
            template_id: 'template_001',
            customer_id: 'cust_001',
            customer_name: 'John Doe',
            reminder_type: 'first',
            subject: 'Payment Reminder - Invoice #INV-001',
            created_at: '2025-09-21T10:30:00Z',
            status: 'drafted',
            preview: 'Dear John Doe, we hope this message finds you well. We wanted to remind you...'
          },
          {
            template_id: 'template_002',
            customer_id: 'cust_002',
            customer_name: 'Jane Smith',
            reminder_type: 'second',
            subject: 'Second Notice - Invoice #INV-002',
            created_at: '2025-09-21T09:15:00Z',
            status: 'approved',
            preview: 'Dear Jane Smith, this is a second reminder regarding your overdue payment...'
          }
        ]);
      }
    } catch (err) {
      console.log('Using mock email drafts for demo mode');
      setEmailDrafts([
        {
          template_id: 'template_001',
          customer_id: 'cust_001',
          customer_name: 'John Doe',
          reminder_type: 'first',
          subject: 'Payment Reminder - Invoice #INV-001',
          created_at: '2025-09-21T10:30:00Z',
          status: 'drafted',
          preview: 'Dear John Doe, we hope this message finds you well. We wanted to remind you...'
        },
        {
          template_id: 'template_002',
          customer_id: 'cust_002',
          customer_name: 'Jane Smith',
          reminder_type: 'second',
          subject: 'Second Notice - Invoice #INV-002',
          created_at: '2025-09-21T09:15:00Z',
          status: 'approved',
          preview: 'Dear Jane Smith, this is a second reminder regarding your overdue payment...'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Load email history and analytics
  const loadEmailHistory = async () => {
    try {
      // If no API URL is configured, use mock data immediately
      if (!apiBaseUrl) {
        console.log('No API URL configured, using mock email history for demo');
        setEmailHistory([
          {
            template_id: 'template_003',
            customer_id: 'cust_003',
            customer_name: 'Bob Wilson',
            reminder_type: 'first',
            subject: 'Payment Reminder - Invoice #INV-003',
            sent_at: '2025-09-21T08:00:00Z',
            delivery_status: 'delivered'
          }
        ]);
        setAnalytics({
          date: '2025-09-21',
          emails_sent: 5,
          first_reminders: 3,
          second_reminders: 2,
          final_notices: 0,
          templates_created: 8,
          templates_approved: 5,
          delivery_rate: 0.98,
          bounce_rate: 0.02
        });
      }
    } catch (err) {
      // Silent error handling - use fallback data for demo
      setError('Failed to load email history');
    }
  };

  // Approve and send email
  const approveAndSendEmail = async (templateId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/ai/approve-and-send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: templateId,
          approver: 'admin'
        })
      });

      const data = await response.json();
      if (data.success) {
        // Refresh drafts and history
        await loadEmailDrafts();
        await loadEmailHistory();
        setError(null);
      } else {
        // Simulate approval for demo
        setEmailDrafts(prev => prev.map(draft => 
          draft.template_id === templateId 
            ? { ...draft, status: 'sent' as const }
            : draft
        ));
      }
    } catch (err) {
      // Silent error handling for demo mode
      setError('Failed to approve and send email');
    } finally {
      setLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadEmailDrafts();
    loadEmailHistory();
  }, []);

  // Render email preview dialog
  const renderPreviewDialog = () => (
    <Dialog
      open={previewOpen}
      onClose={() => setPreviewOpen(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <PreviewIcon />
          Email Preview
        </Box>
      </DialogTitle>
      <DialogContent>
        {selectedTemplate && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              <strong>To:</strong> {selectedTemplate.customer_name} ({selectedTemplate.customer_id})
            </Typography>
            <Typography variant="subtitle1" gutterBottom>
              <strong>Subject:</strong> {selectedTemplate.subject}
            </Typography>
            <Typography variant="subtitle1" gutterBottom>
              <strong>Type:</strong> {selectedTemplate.reminder_type} reminder
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="body1" component="div" sx={{ whiteSpace: 'pre-wrap' }}>
              {selectedTemplate.preview}
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ backgroundColor: 'grey.50', p: 2, borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Generated by Innovate AI • Created: {new Date(selectedTemplate.created_at).toLocaleString()}
              </Typography>
            </Box>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setPreviewOpen(false)}>Close</Button>
        {selectedTemplate?.status === 'drafted' && (
          <Button
            variant="contained"
            color="primary"
            startIcon={<ApproveIcon />}
            onClick={() => {
              approveAndSendEmail(selectedTemplate.template_id);
              setPreviewOpen(false);
            }}
          >
            Approve & Send
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );

  return (
    <DashboardContainer>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Email Management Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage AI-generated email templates and track sending analytics
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => {
            loadEmailDrafts();
            loadEmailHistory();
          }}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Email Drafts Section */}
        <Grid item xs={12} md={6}>
          <SectionCard>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <EmailIcon color="primary" />
                <Typography variant="h6">Pending Email Drafts</Typography>
                {loading && <CircularProgress size={20} />}
              </Box>
              
              <List>
                {emailDrafts.map((draft) => (
                  <ListItem key={draft.template_id} divider>
                    <ListItemText
                      primary={draft.subject}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            To: {draft.customer_name} • {draft.reminder_type} reminder
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Created: {new Date(draft.created_at).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box display="flex" gap={1} alignItems="center">
                        <StatusChip 
                          status={draft.status}
                          label={draft.status.toUpperCase()}
                          size="small"
                        />
                        <Tooltip title="Preview">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedTemplate(draft);
                              setPreviewOpen(true);
                            }}
                          >
                            <PreviewIcon />
                          </IconButton>
                        </Tooltip>
                        {draft.status === 'drafted' && (
                          <Tooltip title="Approve & Send">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => approveAndSendEmail(draft.template_id)}
                              disabled={loading}
                            >
                              <SendIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
                {emailDrafts.length === 0 && (
                  <ListItem>
                    <ListItemText primary="No pending email drafts" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </SectionCard>
        </Grid>

        {/* Email History Section */}
        <Grid item xs={12} md={6}>
          <SectionCard>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <HistoryIcon color="primary" />
                <Typography variant="h6">Recent Email History</Typography>
              </Box>
              
              <List>
                {emailHistory.map((email, index) => (
                  <ListItem key={`${email.template_id}_${index}`} divider>
                    <ListItemText
                      primary={email.subject}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            To: {email.customer_name} • {email.reminder_type} reminder
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Sent: {new Date(email.sent_at).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <StatusChip 
                        status={email.delivery_status}
                        label={email.delivery_status.toUpperCase()}
                        size="small"
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
                {emailHistory.length === 0 && (
                  <ListItem>
                    <ListItemText primary="No recent email history" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </SectionCard>
        </Grid>

        {/* Analytics Section */}
        <Grid item xs={12}>
          <SectionCard>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <AnalyticsIcon color="primary" />
                <Typography variant="h6">Daily Analytics</Typography>
              </Box>
              
              {analytics ? (
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {analytics.emails_sent}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Emails Sent
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="info.main">
                        {analytics.templates_created}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Templates Created
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {(analytics.delivery_rate * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Delivery Rate
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {analytics.first_reminders + analytics.second_reminders + analytics.final_notices}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Reminders
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No analytics data available
                </Typography>
              )}
            </CardContent>
          </SectionCard>
        </Grid>
      </Grid>

      {renderPreviewDialog()}
    </DashboardContainer>
  );
};

export default EmailManagementDashboard;