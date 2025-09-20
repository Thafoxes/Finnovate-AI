import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Alert,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  SmartToy as BotIcon,
  Analytics as AnalyticsIcon,
  Payment as PaymentIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import AIPaymentChatbot from '../components/AIPaymentChatbot';

// Types for dashboard data
interface DashboardStats {
  overdueInvoices: {
    count: number;
    totalAmount: number;
    averageDaysOverdue: number;
  };
  activeCampaigns: {
    count: number;
    successRate: number;
    responseRate: number;
  };
  aiPerformance: {
    totalInteractions: number;
    resolutionRate: number;
    escalationRate: number;
  };
  recentActivity: ActivityItem[];
}

interface ActivityItem {
  id: string;
  type: 'payment' | 'campaign' | 'escalation' | 'resolution';
  description: string;
  timestamp: Date;
  amount?: number;
  customerName?: string;
}

// Styled components
const StatsCard = styled(Card)(({ theme }) => ({
  height: '100%',
  transition: 'transform 0.2s',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4]
  }
}));

const PageHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
  color: theme.palette.primary.contrastText,
  borderRadius: theme.spacing(2),
  marginBottom: theme.spacing(3)
}));

const AIAssistantPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [dashboardData, setDashboardData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Mock data loading
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock data
    const mockData: DashboardStats = {
      overdueInvoices: {
        count: 47,
        totalAmount: 234567.89,
        averageDaysOverdue: 28
      },
      activeCampaigns: {
        count: 12,
        successRate: 73.5,
        responseRate: 89.2
      },
      aiPerformance: {
        totalInteractions: 156,
        resolutionRate: 68.4,
        escalationRate: 15.2
      },
      recentActivity: [
        {
          id: '1',
          type: 'payment',
          description: 'Payment received for Invoice #INV-2024-001',
          timestamp: new Date(Date.now() - 1000 * 60 * 30),
          amount: 15750.00,
          customerName: 'Tech Solutions Inc.'
        },
        {
          id: '2',
          type: 'resolution',
          description: 'AI successfully resolved payment inquiry',
          timestamp: new Date(Date.now() - 1000 * 60 * 45),
          customerName: 'Global Manufacturing LLC'
        },
        {
          id: '3',
          type: 'campaign',
          description: 'New payment campaign created',
          timestamp: new Date(Date.now() - 1000 * 60 * 60),
          customerName: 'Retail Partners Co.'
        },
        {
          id: '4',
          type: 'escalation',
          description: 'Case escalated to human agent',
          timestamp: new Date(Date.now() - 1000 * 60 * 90),
          customerName: 'Industrial Services Ltd.'
        }
      ]
    };
    
    setDashboardData(mockData);
    setLoading(false);
    setLastRefresh(new Date());
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'payment': return <PaymentIcon color="success" />;
      case 'campaign': return <TrendingUpIcon color="primary" />;
      case 'escalation': return <WarningIcon color="warning" />;
      case 'resolution': return <CheckIcon color="success" />;
      default: return <BotIcon />;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'payment': return 'success';
      case 'campaign': return 'primary';
      case 'escalation': return 'warning';
      case 'resolution': return 'success';
      default: return 'default';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 60) {
      return `${diffMins} minutes ago`;
    }
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) {
      return `${diffHours} hours ago`;
    }
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} days ago`;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Page Header */}
      <PageHeader>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <BotIcon sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h4" component="h1" gutterBottom>
                AI Payment Assistant
              </Typography>
              <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
                Intelligent payment collection and customer support powered by Amazon Bedrock
              </Typography>
            </Box>
          </Box>
          
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              Last updated: {lastRefresh.toLocaleTimeString()}
            </Typography>
            <Tooltip title="Refresh data">
              <IconButton 
                onClick={loadDashboardData} 
                disabled={loading}
                sx={{ color: 'inherit' }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </PageHeader>

      {/* Navigation Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="AI Assistant" icon={<BotIcon />} />
          <Tab label="Analytics" icon={<AnalyticsIcon />} />
          <Tab label="Activity" icon={<TrendingUpIcon />} />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Box>
          {/* AI Assistant Interface */}
          <AIPaymentChatbot />
        </Box>
      )}

      {activeTab === 1 && (
        <Box>
          {/* Analytics Dashboard */}
          <Grid container spacing={3}>
            {/* Overview Stats */}
            <Grid item xs={12} md={4}>
              <StatsCard>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <WarningIcon color="warning" sx={{ fontSize: 40 }} />
                    <Box>
                      <Typography variant="h4" color="warning.main">
                        {dashboardData?.overdueInvoices.count || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Overdue Invoices
                      </Typography>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Box>
                    <Typography variant="h6" color="text.primary">
                      {formatCurrency(dashboardData?.overdueInvoices.totalAmount || 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Amount • Avg {dashboardData?.overdueInvoices.averageDaysOverdue || 0} days overdue
                    </Typography>
                  </Box>
                </CardContent>
              </StatsCard>
            </Grid>

            <Grid item xs={12} md={4}>
              <StatsCard>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <TrendingUpIcon color="primary" sx={{ fontSize: 40 }} />
                    <Box>
                      <Typography variant="h4" color="primary.main">
                        {dashboardData?.activeCampaigns.count || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Active Campaigns
                      </Typography>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Success Rate: {dashboardData?.activeCampaigns.successRate || 0}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Response Rate: {dashboardData?.activeCampaigns.responseRate || 0}%
                    </Typography>
                  </Box>
                </CardContent>
              </StatsCard>
            </Grid>

            <Grid item xs={12} md={4}>
              <StatsCard>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <BotIcon color="success" sx={{ fontSize: 40 }} />
                    <Box>
                      <Typography variant="h4" color="success.main">
                        {dashboardData?.aiPerformance.totalInteractions || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        AI Interactions Today
                      </Typography>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Resolution Rate: {dashboardData?.aiPerformance.resolutionRate || 0}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Escalation Rate: {dashboardData?.aiPerformance.escalationRate || 0}%
                    </Typography>
                  </Box>
                </CardContent>
              </StatsCard>
            </Grid>

            {/* Performance Charts Placeholder */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3, textAlign: 'center', minHeight: 300 }}>
                <Typography variant="h6" gutterBottom>
                  Performance Analytics
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Charts and detailed analytics will be displayed here.
                  Integration with chart libraries like Chart.js or D3 recommended.
                </Typography>
                <Box sx={{ mt: 3 }}>
                  <Alert severity="info">
                    Connect to your analytics service or implement chart components
                    to visualize payment collection performance, AI interaction trends,
                    and customer engagement metrics.
                  </Alert>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}

      {activeTab === 2 && (
        <Box>
          {/* Recent Activity */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            
            {dashboardData?.recentActivity && dashboardData.recentActivity.length > 0 ? (
              <Box>
                {dashboardData.recentActivity.map((activity) => (
                  <Box key={activity.id} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Box display="flex" alignItems="center" gap={2}>
                      {getActivityIcon(activity.type)}
                      <Box flex={1}>
                        <Typography variant="body1">
                          {activity.description}
                        </Typography>
                        <Box display="flex" alignItems="center" gap={2} sx={{ mt: 0.5 }}>
                          {activity.customerName && (
                            <Chip 
                              label={activity.customerName} 
                              size="small" 
                              variant="outlined"
                            />
                          )}
                          {activity.amount && (
                            <Chip 
                              label={formatCurrency(activity.amount)}
                              size="small"
                              color="success"
                              variant="outlined"
                            />
                          )}
                          <Chip
                            label={activity.type.toUpperCase()}
                            size="small"
                            color={getActivityColor(activity.type) as any}
                            variant="outlined"
                          />
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {formatTimeAgo(activity.timestamp)}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Alert severity="info">
                No recent activity to display.
              </Alert>
            )}
          </Paper>
        </Box>
      )}
    </Box>
  );
};

export default AIAssistantPage;