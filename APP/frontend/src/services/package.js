import axios from '../utils/axios';

export const createPackage = async (packageData) => {
    const response = await axios.post('/api/packages', packageData);
    return response.data;
};

export const getPackageDetails = async (package_sk) => {
    const response = await axios.get(`/api/packages/${package_sk}`);
    return response.data;
};

export const listPackages = async () => {
    const response = await axios.get('/api/packages');
    return response.data;
};