import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createApi, getApiDetails, updateApi } from '../../services/api';

const ApiManagement = ({ api_sk = null }) => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        api_name: '',
        location_sk: '',
        batch_sk: '',
        documents: []
    });
    const [locations, setLocations] = useState([]);
    const [batches, setBatches] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            if (api_sk) {
                try {
                    const apiData = await getApiDetails(api_sk);
                    setFormData({
                        api_name: apiData.header.api_name,
                        location_sk: apiData.header.location_fk,
                        batch_sk: apiData.header.batch_sk,
                        documents: apiData.details.map(d => ({
                            document_sk: d.document_sk,
                            blob_link: d.blob_link
                        }))
                    });
                } catch (err) {
                    setError('Failed to load API details');
                }
            }
        };

        loadData();
    }, [api_sk]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            if (api_sk) {
                await updateApi(api_sk, formData);
            } else {
                await createApi(formData);
            }
            navigate('/apis');
        } catch (err) {
            setError(err.response?.data?.error || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleDocumentAdd = () => {
        setFormData(prev => ({
            ...prev,
            documents: [...prev.documents, { document_sk: '', blob_link: '' }]
        }));
    };

    const handleDocumentRemove = (index) => {
        setFormData(prev => ({
            ...prev,
            documents: prev.documents.filter((_, i) => i !== index)
        }));
    };

    return (
        <div className="max-w-2xl mx-auto p-6">
            <h2 className="text-2xl font-bold mb-6">
                {api_sk ? 'Edit API' : 'Create New API'}
            </h2>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <label className="block text-sm font-medium text-gray-700">
                        API Name
                    </label>
                    <input
                        type="text"
                        value={formData.api_name}
                        onChange={(e) => setFormData(prev => ({
                            ...prev,
                            api_name: e.target.value
                        }))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        required
                    />
                </div>

                {/* Add more form fields for location and batch */}

                <div>
                    <h3 className="text-lg font-medium text-gray-700 mb-2">
                        Documents
                    </h3>
                    {formData.documents.map((doc, index) => (
                        <div key={index} className="flex gap-4 mb-4">
                            <input
                                type="text"
                                placeholder="Document SK"
                                value={doc.document_sk}
                                onChange={(e) => {
                                    const newDocs = [...formData.documents];
                                    newDocs[index].document_sk = e.target.value;
                                    setFormData(prev => ({
                                        ...prev,
                                        documents: newDocs
                                    }));
                                }}
                                className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            />
                            <input
                                type="text"
                                placeholder="Blob Link"
                                value={doc.blob_link}
                                onChange={(e) => {
                                    const newDocs = [...formData.documents];
                                    newDocs[index].blob_link = e.target.value;
                                    setFormData(prev => ({
                                        ...prev,
                                        documents: newDocs
                                    }));
                                }}
                                className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            />
                            <button
                                type="button"
                                onClick={() => handleDocumentRemove(index)}
                                className="text-red-600 hover:text-red-900"
                            >
                                Remove
                            </button>
                        </div>
                    ))}
                    <button
                        type="button"
                        onClick={handleDocumentAdd}
                        className="mt-2 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Add Document
                    </button>
                </div>

                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={loading}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        {loading ? 'Saving...' : 'Save API'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ApiManagement;