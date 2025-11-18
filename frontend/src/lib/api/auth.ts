import { api } from './client';

export interface LoginRequest {
  username: string; // OAuth2PasswordRequestForm expects username, but we use email as username
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    // FastAPI OAuth2PasswordRequestForm expects form-data, not JSON
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('password', data.password);
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/users/me');
    return response.data;
  },

  logout: async () => {
    // We just remove tokens on client side usually, but if there is an endpoint:
    // await api.post('/auth/logout'); 
    localStorage.removeItem('token');
  },
};
