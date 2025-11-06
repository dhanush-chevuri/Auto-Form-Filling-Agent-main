import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL 
  ? `${process.env.REACT_APP_API_URL}/api` 
  : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const parseResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return api.post('/parse-resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const analyzeForm = async (formUrl) => {
  return api.post('/analyze-form', { form_url: formUrl });
};

export const fillForm = async (file, formUrl) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('form_url', formUrl);
  
  return api.post('/fill-form', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const healthCheck = async () => {
  return api.get('/health');
};