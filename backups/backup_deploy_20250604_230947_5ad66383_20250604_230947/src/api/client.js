import axios from 'axios';

const API_BASE_URL = 'https://your-api-domain.com';

export const fetchTasks = async () => {
  return axios.get(`${API_BASE_URL}/tasks`);
};

export const createTask = async (taskData) => {
  return axios.post(`${API_BASE_URL}/tasks`, taskData);
};

// Add more API calls as needed