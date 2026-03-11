import axios from '../utils/axios';

export const getSubscriptionInfo = async () => {
    const response = await axios.get('/api/subscription');
    return response.data;
};

export const getApiUsage = async () => {
    const response = await axios.get('/api/usage');
    return response.data;
};

export const upgradeSubscription = async (tierId) => {
    const response = await axios.post('/api/subscription/upgrade', { tierId });
    return response.data;
};

export const generateApiKey = async () => {
    const response = await axios.post('/api/keys/generate');
    return response.data;
};

export const listApiKeys = async () => {
    const response = await axios.get('/api/keys');
    return response.data;
};

export const revokeApiKey = async (keyId) => {
    const response = await axios.delete(`/api/keys/${keyId}`);
    return response.data;
};