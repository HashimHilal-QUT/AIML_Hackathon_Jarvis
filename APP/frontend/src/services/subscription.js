import axios from '../utils/axios';

export const getSubscriptionTiers = async () => {
    const response = await axios.get('/api/subscription/tiers');
    return response.data;
};

export const getCurrentUsage = async () => {
    const response = await axios.get('/api/subscription/usage');
    return response.data;
};

export const upgradeSubscription = async (tierId) => {
    const response = await axios.post('/api/subscription/upgrade', { tier_id: tierId });
    return response.data;
};