import React from 'react';
import { Tooltip, IconButton } from '@mui/material';
import { HelpOutline } from '@mui/icons-material';

interface HelpTooltipProps {
  title: string;
  size?: 'small' | 'medium';
}

const HelpTooltip: React.FC<HelpTooltipProps> = ({ title, size = 'small' }) => {
  return (
    <Tooltip title={title} arrow placement="top">
      <IconButton size={size} sx={{ ml: 0.5 }}>
        <HelpOutline fontSize="small" color="action" />
      </IconButton>
    </Tooltip>
  );
};

export default HelpTooltip;