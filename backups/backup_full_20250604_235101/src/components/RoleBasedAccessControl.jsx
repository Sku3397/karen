// RoleBasedAccessControl.jsx
import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

// Sample data, to be replaced with Firestore/API integration
const users = [
  { name: 'admin@site.com', role: 'Admin' },
  { name: 'ops@site.com', role: 'Operator' },
  { name: 'viewer@site.com', role: 'Viewer' }
];

const roleColors = {
  'Admin': 'primary',
  'Operator': 'secondary',
  'Viewer': 'default'
};

const RoleBasedAccessControl = () => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>Role-Based Access Control</Typography>
      <List>
        {users.map(user => (
          <ListItem key={user.name} secondaryAction={
            <Chip label={user.role} color={roleColors[user.role]} size="small" />
          }>
            <ListItemText primary={user.name} />
          </ListItem>
        ))}
      </List>
    </CardContent>
  </Card>
);

export default RoleBasedAccessControl;
