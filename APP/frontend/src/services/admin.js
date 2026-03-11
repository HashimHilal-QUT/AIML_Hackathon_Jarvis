import axios from '../utils/axios';

export const getAuditLogs = async () => {
    const response = await axios.get('/api/admin/audit-logs');
    return response.data;
};

export const getApiUsageLogs = async () => {
    const response = await axios.get('/api/admin/usage-logs');
    return response.data;
};