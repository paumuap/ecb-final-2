import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface User {
  username: string;
  email: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface Patient {
  id?: number;
  nom: string;
  cognom: string;
  email: string;
  data_naixement: string;
  numero_historia: string;
}

export const authAPI = {
  register: (username: string, email: string, password: string, role: string = 'user') =>
    api.post<User>('/register', { username, email, password, role }),
  login: (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return axios.post<LoginResponse>(`${API_BASE_URL}/login`, formData);
  },
  getMe: () => api.get<User>('/me'),
};

export const patientAPI = {
  list: () => api.get<Patient[]>('/pacients'),
  get: (id: number) => api.get<Patient>(`/pacients/${id}`),
  create: (data: Patient) => api.post<Patient>('/pacients', data),
  update: (id: number, data: Patient) => api.put<Patient>(`/pacients/${id}`, data),
  delete: (id: number) => api.delete(`/pacients/${id}`),
};

export const adminAPI = {
  listUsers: () => api.get<User[]>('/admin/users'),
  createUser: (username: string, email: string, password: string, role: string) =>
    api.post<User>('/admin/users', { username, email, password, role }),
  listAllPatients: () => api.get<Patient[]>('/admin/pacients'),
};

export default api;
