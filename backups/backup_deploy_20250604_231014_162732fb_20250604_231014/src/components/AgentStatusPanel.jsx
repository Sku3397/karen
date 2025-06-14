// AgentStatusPanel.jsx
import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

// Sample data, to be replaced with Firestore API integration
const agents = [
  { name: 'Agent 001', status: 'Online' },
  { name: 'Agent 002', status: 'Busy' },
  { name: 'Agent 003', status: 'Offline' }
];

const statusColors = {
  'Online': 'success',
  'Busy': 'warning',
  'Offline': 'default'
};

const AgentStatusPanel = () => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>Agent Statuses</Typography>
      <List>
        {agents.map(agent => (
          <ListItem key={agent.name} secondaryAction={
            <Chip label={agent.status} color={statusColors[agent.status]} size="small" />
          }>
            <ListItemText primary={agent.name} />
          </ListItem>
        ))}
      </List>
    </CardContent>
  </Card>
);

export default AgentStatusPanel;
