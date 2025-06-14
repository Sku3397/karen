// EmergencyAlertsPanel.jsx
import React from 'react';
import { Card, CardContent, Typography, Alert, Stack } from '@mui/material';

// Sample data, to be replaced with Firestore/API integration
const alerts = [
  { message: 'Agent 002 failed to complete task T-102', severity: 'error' },
  { message: 'Payment gateway latency detected', severity: 'warning' }
];

const EmergencyAlertsPanel = () => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>Emergency Alerts</Typography>
      <Stack spacing={2}>
        {alerts.map((alert, idx) => (
          <Alert severity={alert.severity} key={idx}>{alert.message}</Alert>
        ))}
      </Stack>
    </CardContent>
  </Card>
);

export default EmergencyAlertsPanel;
