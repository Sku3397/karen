// BillingInfoPanel.jsx
import React from 'react';
import { Card, CardContent, Typography, Table, TableBody, TableCell, TableRow } from '@mui/material';

// Sample data, to be replaced with Firestore/API integration
const billing = [
  { provider: 'Stripe', period: 'June', amount: '$120.00', status: 'Paid' },
  { provider: 'PayPal', period: 'June', amount: '$45.00', status: 'Pending' }
];

const BillingInfoPanel = () => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>Billing Info</Typography>
      <Table size="small">
        <TableBody>
          {billing.map((item, idx) => (
            <TableRow key={idx}>
              <TableCell>{item.provider}</TableCell>
              <TableCell>{item.period}</TableCell>
              <TableCell>{item.amount}</TableCell>
              <TableCell>{item.status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </CardContent>
  </Card>
);

export default BillingInfoPanel;
