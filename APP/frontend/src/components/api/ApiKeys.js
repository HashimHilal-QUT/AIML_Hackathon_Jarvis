import React, { useState, useEffect } from 'react';
import { generateApiKey, listApiKeys, revokeApiKey } from '../../services/api';

const ApiKeys = () => {
    const [apiKeys, setApiKeys] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadApiKeys = async () => {
        try {
            const keys = await listApiKeys();
            setApiKeys(keys);
        } catch (err) {
            setError('Failed to load API keys');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadApiKeys();
    }, []);

    const handleGenerateKey = async () => {
        try {
            const newKey = await generateApiKey();
            setApiKeys([...apiKeys, newKey]);
        } catch (err) {
            setError('Failed to generate API key');
        }
    };

    const handleRevokeKey = async (keyId) => {
        try {
            await revokeApiKey(keyId);
            setApiKeys(apiKeys.filter(key => key.key_id !== keyId));
        } catch (err) {
            setError('Failed to revoke API key');
        }
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">API Keys</h2>
                <button
                    onClick={handleGenerateKey}
                    className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
                >
                    Generate New Key
                </button>
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                API Key
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Created
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {apiKeys.map((key) => (
                            <tr key={key.key_id}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <code className="text-sm">{key.api_key}</code>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {new Date(key.created_at).toLocaleDateString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                        key.is_active
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-red-100 text-red-800'
                                    }`}>
                                        {key.is_active ? 'Active' : 'Revoked'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {key.is_active && (
                                        <button
                                            onClick={() => handleRevokeKey(key.key_id)}
                                            className="text-red-600 hover:text-red-900"
                                        >
                                            Revoke
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ApiKeys;