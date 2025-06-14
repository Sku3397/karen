// TaskProgressPanel.jsx
import React from 'react';
import { Card, CardContent, Typography, LinearProgress, Box } from '@mui/material';

// Sample data, to be replaced with Firestore API integration
const tasks = [
  { id: 'T-101', desc: 'Fix virtual lock', progress: 80 },
  { id: 'T-102', desc: 'Install chatbot update', progress: 45 },
  { id: 'T-103', desc: 'Review billing issues', progress: 100 }
];

const TaskProgressPanel = () => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>Task Progress</Typography>
      {tasks.map(task => (
        <Box key={task.id} mb={2}>
          <Typography>{task.desc} ({task.id})</Typography>
          <LinearProgress variant="determinate" value={task.progress} sx={{ height: 8, borderRadius: 4 }} />
        </Box>
      ))}
    </CardContent>
  </Card>
);

export default TaskProgressPanel;
