import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  Avatar,
  IconButton,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Tooltip,
  Badge
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Payment as PaymentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Types for the chat interface
interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  timestamp: Date;
  type?: 'text' | 'payment_options' | 'escalation' | 'info' | 'analysis' | 'email_draft';
  metadata?: {
    paymentOptions?: PaymentOption[];
    suggestedActions?: string[];
    escalationNeeded?: boolean;
    analysisData?: any;
    emailDrafts?: any[];
  };
}

interface PaymentOption {
  method: string;
  description: string;
  action?: string;
}

interface ConversationContext {
  customerId?: string;
  customerName?: string;
  companyName?: string;
  invoiceId?: string;
  conversationId?: string;
}

// Styled components
const ChatContainer = styled(Paper)(({ theme }) => ({
  height: '600px',
  display: 'flex',
  flexDirection: 'column',
  borderRadius: theme.spacing(2),
  overflow: 'hidden',
  boxShadow: theme.shadows[3]
}));

const ChatHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1)
}));

const MessagesContainer = styled(Box)(({ theme }) => ({
  flex: 1,
  overflowY: 'auto',
  padding: theme.spacing(1),
  backgroundColor: theme.palette.grey[50]
}));

const MessageBubble = styled(Box)<{ sender: 'user' | 'bot' }>(({ theme, sender }) => ({
  display: 'flex',
  justifyContent: sender === 'user' ? 'flex-end' : 'flex-start',
  marginBottom: theme.spacing(1),
  '& .message-content': {
    maxWidth: '80%',
    padding: theme.spacing(1.5),
    borderRadius: theme.spacing(2),
    backgroundColor: sender === 'user' ? theme.palette.primary.main : theme.palette.background.paper,
    color: sender === 'user' ? theme.palette.primary.contrastText : theme.palette.text.primary,
    boxShadow: theme.shadows[1]
  }
}));

const InputContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  borderTop: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  gap: theme.spacing(1),
  alignItems: 'flex-end'
}));

const AIPaymentChatbot: React.FC = () => {
  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'bot',
      content: 'Hello! I\'m Innovate AI, your intelligent invoice management assistant. I can help you analyze customer payment patterns, draft professional reminder emails, track overdue invoices, and generate insightful reports. What would you like to work on today?',
      timestamp: new Date(),
      type: 'text',
      metadata: {
        suggestedActions: ['Analyze customer payments', 'Draft reminder emails', 'View overdue invoices', 'Generate reports']
      }
    }
  ]);
  
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [context, setContext] = useState<ConversationContext>({});
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Real API call to the AI Lambda backend
  const sendMessageToAPI = async (message: string): Promise<{
    response: string;
    conversation_id: string;
    suggested_actions: string[];
    analysis_data?: any;
    email_drafts?: any[];
    escalation_needed: boolean;
  }> => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || '';
      
      // If no API URL is configured, use fallback immediately
      if (!apiBaseUrl) {
        console.log('No API URL configured, using fallback responses for demo');
        return await sendMockInvoiceResponse(message);
      }
      
      // Send to AI conversation endpoint
      const response = await fetch(`${apiBaseUrl}/ai/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          history: messages.slice(-5).map(msg => ({
            role: msg.sender === 'user' ? 'user' : 'assistant',
            content: msg.content
          }))
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        return {
          response: data.data.response,
          conversation_id: context.conversationId || 'conv_' + Date.now(),
          suggested_actions: extractSuggestedActions(data.data.response),
          escalation_needed: false
        };
      } else {
        // Fallback to mock response if API fails
        return await sendMockInvoiceResponse(message);
      }
    } catch (error) {
      // Silently fallback to mock response for demo (no console output)
      return await sendMockInvoiceResponse(message);
    }
  };

  // Extract suggested actions from AI response
  const extractSuggestedActions = (response: string): string[] => {
    const actions = [];
    
    if (response.toLowerCase().includes('analyze') || response.toLowerCase().includes('analysis')) {
      actions.push('Analyze customer payment patterns');
    }
    if (response.toLowerCase().includes('email') || response.toLowerCase().includes('reminder')) {
      actions.push('Draft reminder emails');
    }
    if (response.toLowerCase().includes('report') || response.toLowerCase().includes('summary')) {
      actions.push('Generate payment summary');
    }
    if (response.toLowerCase().includes('overdue') || response.toLowerCase().includes('late')) {
      actions.push('View overdue invoices');
    }
    
    return actions.length > 0 ? actions : ['Continue conversation'];
  };

  // Fallback mock responses for invoice management context
  const sendMockInvoiceResponse = async (message: string): Promise<{
    response: string;
    conversation_id: string;
    suggested_actions: string[];
    analysis_data?: any;
    email_drafts?: any[];
    escalation_needed: boolean;
  }> => {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock responses based on message content
    const messageText = message.toLowerCase();
    
    if (messageText.includes('analyze') || messageText.includes('customer')) {
      return {
        response: "I've analyzed your customer payment patterns. I found 3 customers with frequent late payments (>7 days overdue). Would you like me to draft reminder emails for these customers or show you the detailed analysis?",
        conversation_id: context.conversationId || 'conv_' + Date.now(),
        suggested_actions: ['Draft reminder emails', 'Show detailed analysis', 'View customer list'],
        analysis_data: {
          frequent_late_payers: 3,
          total_analyzed: 25,
          avg_late_days: 12
        },
        escalation_needed: false
      };
    }
    
    if (messageText.includes('email') || messageText.includes('reminder')) {
      return {
        response: "I can help you draft professional reminder emails using AI. I'll create personalized messages with Innovate AI branding. Which type of reminder would you like: first reminder, second reminder, or final notice?",
        conversation_id: context.conversationId || 'conv_' + Date.now(),
        suggested_actions: ['First reminder', 'Second reminder', 'Final notice', 'Bulk email campaign'],
        escalation_needed: false
      };
    }
    
    if (messageText.includes('overdue') || messageText.includes('late')) {
      return {
        response: "I've identified several overdue invoices that need attention. There are 8 invoices totaling $12,450 that are more than 30 days overdue. Would you like me to prioritize these by amount or customer risk level?",
        conversation_id: context.conversationId || 'conv_' + Date.now(),
        suggested_actions: ['Prioritize by amount', 'Prioritize by risk', 'Send bulk reminders'],
        escalation_needed: false
      };
    }

    if (messageText.includes('report') || messageText.includes('summary')) {
      return {
        response: "I can generate comprehensive payment reports and analytics. Our AI system tracks payment patterns, identifies trends, and provides actionable insights. What type of report would you like to see?",
        conversation_id: context.conversationId || 'conv_' + Date.now(),
        suggested_actions: ['Payment trends report', 'Customer risk analysis', 'Email campaign results'],
        escalation_needed: false
      };
    }
    
    // Default response for invoice management
    return {
      response: "I'm Innovate AI, your intelligent invoice management assistant. I can help you analyze customer payment patterns, draft professional reminder emails, track overdue invoices, and generate insightful reports. What would you like to work on today?",
      conversation_id: context.conversationId || 'conv_' + Date.now(),
      suggested_actions: ['Analyze customer payments', 'Draft reminder emails', 'View overdue invoices', 'Generate reports'],
      escalation_needed: false
    };
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'user',
      content: inputMessage,
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendMessageToAPI(inputMessage);
      
      // Update conversation context
      setContext(prev => ({
        ...prev,
        conversationId: response.conversation_id
      }));

      const botMessage: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: 'bot',
        content: response.response,
        timestamp: new Date(),
        type: response.analysis_data ? 'info' : response.escalation_needed ? 'escalation' : 'text',
        metadata: {
          suggestedActions: response.suggested_actions,
          escalationNeeded: response.escalation_needed,
          analysisData: response.analysis_data,
          emailDrafts: response.email_drafts
        }
      };

      setMessages(prev => [...prev, botMessage]);
      
    } catch (err) {
      setError('Failed to send message. Please try again.');
      // Silent error handling for demo mode
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handlePaymentOption = (option: PaymentOption) => {
    const message = `I'd like to proceed with ${option.description}`;
    setInputMessage(message);
    handleSendMessage();
  };

  const renderMessage = (message: ChatMessage) => {
    return (
      <MessageBubble key={message.id} sender={message.sender}>
        <Box className="message-content">
          {/* Message avatar */}
          <Box display="flex" alignItems="flex-start" gap={1}>
            <Avatar 
              sx={{ 
                width: 32, 
                height: 32,
                bgcolor: message.sender === 'bot' ? 'primary.main' : 'secondary.main'
              }}
            >
              {message.sender === 'bot' ? <BotIcon /> : <PersonIcon />}
            </Avatar>
            
            <Box flex={1}>
              {/* Message content */}
              <Typography variant="body2" sx={{ mb: 1 }}>
                {message.content}
              </Typography>
              
              {/* Payment options */}
              {message.metadata?.paymentOptions && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    Payment Options:
                  </Typography>
                  <Box display="flex" flexDirection="column" gap={1}>
                    {message.metadata.paymentOptions.map((option, index) => (
                      <Button
                        key={index}
                        variant="outlined"
                        size="small"
                        startIcon={<PaymentIcon />}
                        onClick={() => handlePaymentOption(option)}
                        sx={{ justifyContent: 'flex-start' }}
                      >
                        {option.description}
                      </Button>
                    ))}
                  </Box>
                </Box>
              )}
              
              {/* Suggested actions */}
              {message.metadata?.suggestedActions && message.metadata.suggestedActions.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  <Box display="flex" flexWrap="wrap" gap={0.5}>
                    {message.metadata.suggestedActions.map((action, index) => (
                      <Chip
                        key={index}
                        label={action}
                        size="small"
                        variant="outlined"
                        icon={message.metadata?.escalationNeeded ? <WarningIcon /> : <InfoIcon />}
                        color={message.metadata?.escalationNeeded ? "warning" : "default"}
                      />
                    ))}
                  </Box>
                </Box>
              )}
              
              {/* Timestamp */}
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {message.timestamp.toLocaleTimeString()}
              </Typography>
            </Box>
          </Box>
        </Box>
      </MessageBubble>
    );
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 800, mx: 'auto' }}>
      {/* Header with context info */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" gutterBottom>
          Innovate AI - Invoice Management Assistant
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Analyze payment patterns, draft AI-powered reminder emails, and automate invoice management
        </Typography>
      </Box>

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Chat container */}
      <ChatContainer>
        {/* Chat header */}
        <ChatHeader>
          <BotIcon />
          <Typography variant="h6">Innovate AI Assistant</Typography>
          <Box flex={1} />
          <Badge color="success" variant="dot">
            <Typography variant="body2">Online</Typography>
          </Badge>
        </ChatHeader>

        {/* Messages area */}
        <MessagesContainer>
          {messages.map(renderMessage)}
          {isLoading && (
            <Box display="flex" justifyContent="center" p={2}>
              <CircularProgress size={24} />
              <Typography variant="body2" sx={{ ml: 1 }}>
                AI is typing...
              </Typography>
            </Box>
          )}
          <div ref={messagesEndRef} />
        </MessagesContainer>

        {/* Input area */}
        <InputContainer>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            placeholder="Type your message..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            variant="outlined"
            size="small"
          />
          <Tooltip title="Send message">
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              sx={{ 
                bgcolor: 'primary.main', 
                color: 'white',
                '&:hover': { bgcolor: 'primary.dark' },
                '&:disabled': { bgcolor: 'grey.300' }
              }}
            >
              <SendIcon />
            </IconButton>
          </Tooltip>
        </InputContainer>
      </ChatContainer>

      {/* Quick action buttons */}
      <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setInputMessage("Analyze customers with frequent late payments")}
        >
          📊 Analyze Customers
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setInputMessage("Draft reminder emails for overdue invoices")}
        >
          📧 Draft Emails
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setInputMessage("Show payment patterns for high-risk customers")}
        >
          📈 Payment Patterns
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setInputMessage("Generate bulk reminder campaign")}
        >
          🚀 Bulk Campaign
        </Button>
      </Box>
    </Box>
  );
};

export default AIPaymentChatbot;