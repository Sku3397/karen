// AdminDashboard.jsx
import React from 'react';
import { Grid, Box, Typography } from '@mui/material';
import AgentStatusPanel from './AgentStatusPanel';
import TaskProgressPanel from './TaskProgressPanel';
import BillingInfoPanel from './BillingInfoPanel';
import EmergencyAlertsPanel from './EmergencyAlertsPanel';
import RoleBasedAccessControl from './RoleBasedAccessControl';

const AdminDashboard = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Admin Dashboard</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <AgentStatusPanel />
        </Grid>
        <Grid item xs={12} md={6}>
          <TaskProgressPanel />
        </Grid>
        <Grid item xs={12} md={6}>
          <BillingInfoPanel />
        </Grid>
        <Grid item xs={12} md={6}>
          <EmergencyAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <RoleBasedAccessControl />
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdminDashboard;
