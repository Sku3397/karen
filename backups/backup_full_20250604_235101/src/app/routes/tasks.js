// Tasks routes
const express = require('express');
const router = express.Router();

// Define the routes for tasks
router.post('/tasks', (req, res) => {});
router.get('/tasks/:taskId', (req, res) => {});
router.put('/tasks/:taskId', (req, res) => {});
router.delete('/tasks/:taskId', (req, res) => {});

module.exports = router;