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
  type?: 'text' | 'payment_options' | 'escalation' | 'info';
  metadata?: {
    paymentOptions?: PaymentOption[];
    suggestedActions?: string[];
    escalationNeeded?: boolean;
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
      content: 'Hello! I\'m your AI payment assistant. I can help you with overdue invoices, payment arrangements, and answering questions about your account. How can I assist you today?',
      timestamp: new Date(),
      type: 'text'
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

  // Real API call to the Lambda backend
  const sendMessageToAPI = async (message: string): Promise<{
    response: string;
    conversation_id: string;
    suggested_actions: string[];
    payment_options?: PaymentOption[];
    escalation_needed: boolean;
  }> => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || '';
      
      const response = await fetch(`${apiBaseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          user_id: context.customerId || 'anonymous',
          conversation_id: context.conversationId
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        return {
          response: data.response,
          conversation_id: data.user_id || context.conversationId || 'conv_' + Date.now(),
          suggested_actions: data.actions || [],
          escalation_needed: false
        };
      } else {
        // Fallback to mock response if API fails
        return await sendMockResponse(message);
      }
    } catch (error) {
      console.error('AI API call failed:', error);
      // Fallback to mock response
      return await sendMockResponse(message);
    }
  };

  // Fallback mock responses for when API is unavailable
  const sendMockResponse = async (message: string): Promise<{
    response: string;
    conversation_id: string;
    suggested_actions: string[];
    payment_options?: PaymentOption[];
    escalation_needed: boolean;
  }> => {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock responses based on message content
    const messageText = message.toLowerCase();
    
    if (messageText.includes('payment') || messageText.includes('pay')) {
      return {
        response: "I understand you'd like to make a payment. I can help you with several options. Would you prefer to pay the full amount or set up a payment plan?",
        conversation_id: context.conversationId || 'conv_' + Date.now(),
        suggested_actions: ['Provide payment options', 'Set up payment plan'],
        payment_options: [
          { method: 'bank_transfer', description: 'Direct bank transfer', action: 'setup_transfer' },
          { method: 'credit_card', description: 'Credit card payment', action: 'process_card' },
          { method: 'payment_plan', description: 'Monthly payment plan', action: 'setup_plan' }
        ],
        escalation_needed: false
      };
    }
    
    if (messageText.includes('problem') || messageText.includes('issue') || messageText.includes('cannot')) {
      return {
        response: "I understand you're experiencing difficulties. Let me connect you with a specialist who can help resolve this issue. In the meantime, would you like me to note any specific concerns about your account?",
        conversation_id: context.conversationId || 'conv_' + Date.now(),
        suggested_actions: ['Escalate to human agent', 'Document concerns'],
        escalation_needed: true
      };
    }
    
    if (messageText.includes('dispute') || messageText.includes('wrong') || messageText.includes('incorrect')) {
      return {
        response: "I see you have concerns about the invoice details. Let me review your account information and escalate this to our billing team for immediate attention. They'll contact you within 24 hours to resolve any discrepancies.",
        conversation_id: context.conversationId || 'conv_' + Date.now(),
        suggested_actions: ['Review invoice details', 'Escalate to billing team'],
        escalation_needed: true
      };
    }
    
    // Default response
    return {
      response: "Thank you for your message. I'm here to help with any payment-related questions or concerns. Can you tell me more about what you need assistance with?",
      conversation_id: context.conversationId || 'conv_' + Date.now(),
      suggested_actions: ['Ask for more details'],
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
        type: response.payment_options ? 'payment_options' : response.escalation_needed ? 'escalation' : 'text',
        metadata: {
          paymentOptions: response.payment_options,
          suggestedActions: response.suggested_actions,
          escalationNeeded: response.escalation_needed
        }
      };

      setMessages(prev => [...prev, botMessage]);
      
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Chat error:', err);
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
          AI Payment Assistant
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Get help with overdue payments, set up payment plans, or resolve billing issues
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
          <Typography variant="h6">Payment Intelligence Assistant</Typography>
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
          onClick={() => setInputMessage("I need help with my overdue payment")}
        >
          Payment Help
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setInputMessage("I want to set up a payment plan")}
        >
          Payment Plan
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setInputMessage("I have a question about my invoice")}
        >
          Invoice Question
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setInputMessage("I need to speak with someone")}
        >
          Human Agent
        </Button>
      </Box>
    </Box>
  );
};

export default AIPaymentChatbot;