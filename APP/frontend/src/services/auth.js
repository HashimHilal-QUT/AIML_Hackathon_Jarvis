import axios from '../utils/axios';

export const registerUser = async (userData) => {
    const response = await axios.post('/auth/register', userData);
    return response.data;
};

export const loginUser = async (email, password) => {
    const response = await axios.post('/auth/login', { email, password });
    return response.data;
};

export const logoutUser = async () => {
    const response = await axios.post('/auth/logout');
    return response.data;
};