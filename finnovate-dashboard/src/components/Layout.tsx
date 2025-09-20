import React from 'react';
import { Box, AppBar, Toolbar, Typography, IconButton, Drawer, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { Menu as MenuIcon, Dashboard, Receipt, People, Warning, Brightness4, Brightness7 } from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { toggleSidebar, toggleTheme } from '../store/slices/uiSlice';
import { RootState } from '../store';
import NotificationCenter from './NotificationCenter';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { sidebarOpen, theme } = useSelector((state: RootState) => state.ui);

  const menuItems = [
    { text: 'Dashboard', icon: <Dashboard />, path: '/' },
    { text: 'Invoices', icon: <Receipt />, path: '/invoices' },
    { text: 'Customers', icon: <People />, path: '/customers' },
    { text: 'Overdue', icon: <Warning />, path: '/overdue' },
  ];

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton color="inherit" onClick={() => dispatch(toggleSidebar())}>
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Finnovate AI Dashboard
          </Typography>
          <NotificationCenter />
          <IconButton color="inherit" onClick={() => dispatch(toggleTheme())}>
            {theme === 'dark' ? <Brightness7 /> : <Brightness4 />}
          </IconButton>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="persistent"
        anchor="left"
        open={sidebarOpen}
        sx={{
          width: 240,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: 240, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} onClick={() => navigate(item.path)} sx={{ cursor: 'pointer' }}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, ml: sidebarOpen ? 0 : -30 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

export default Layout;