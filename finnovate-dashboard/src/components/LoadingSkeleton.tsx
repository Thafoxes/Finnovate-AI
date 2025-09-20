import React from 'react';
import { Skeleton, Box, Card, CardContent } from '@mui/material';

export const CardSkeleton: React.FC = () => (
  <Card>
    <CardContent>
      <Skeleton variant="text" width="60%" height={24} />
      <Skeleton variant="text" width="40%" height={32} sx={{ mt: 1 }} />
    </CardContent>
  </Card>
);

export const TableSkeleton: React.FC = () => (
  <Box>
    {[...Array(5)].map((_, i) => (
      <Box key={i} display="flex" alignItems="center" py={2} borderBottom="1px solid #eee">
        <Skeleton variant="text" width="20%" height={20} sx={{ mr: 2 }} />
        <Skeleton variant="text" width="30%" height={20} sx={{ mr: 2 }} />
        <Skeleton variant="text" width="15%" height={20} sx={{ mr: 2 }} />
        <Skeleton variant="text" width="20%" height={20} />
      </Box>
    ))}
  </Box>
);

export const ChartSkeleton: React.FC = () => (
  <Card>
    <CardContent>
      <Skeleton variant="text" width="40%" height={24} sx={{ mb: 2 }} />
      <Skeleton variant="rectangular" width="100%" height={200} />
    </CardContent>
  </Card>
);