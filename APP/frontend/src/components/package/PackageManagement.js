import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPackage, getPackageDetails } from '../../services/package';

const PackageManagement = ({ package_sk = null }) => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        package_name: '',
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
            if (package_sk) {
                try {
                    const packageData = await getPackageDetails(package_sk);
                    setFormData({
                        package_name: packageData.header.package_name,
                        location_sk: packageData.header.location_sk,
                        batch_sk: packageData.header.batch_sk,
                        documents: packageData.details.map(d => ({
                            document_sk: d.document_sk,
                            blob_link: d.blob_link
                        }))
                    });
                } catch (err) {
                    setError('Failed to load package details');
                }
            }
        };

        loadData();
    }, [package_sk]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await createPackage(formData);
            navigate('/packages');
        } catch (err) {
            setError(err.response?.data?.error || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto p-6">
            <h2 className="text-2xl font-bold mb-6">
                {package_sk ? 'Edit Package' : 'Create New Package'}
            </h2>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <label className="block text-sm font-medium text-gray-700">
                        Package Name
                    </label>
                    <input
                        type="text"
                        value={formData.package_name}
                        onChange={(e) => setFormData(prev => ({
                            ...prev,
                            package_name: e.target.value
                        }))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        required
                    />
                </div>

                {/* Location and Batch Selection */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Location
                        </label>
                        <select
                            value={formData.location_sk}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                location_sk: e.target.value
                            }))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            required
                        >
                            <option value="">Select Location</option>
                            {locations.map(loc => (
                                <option key={loc.location_sk} value={loc.location_sk}>
                                    {loc.location_name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Batch
                        </label>
                        <select
                            value={formData.batch_sk}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                batch_sk: e.target.value
                            }))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            required
                        >
                            <option value="">Select Batch</option>
                            {batches.map(batch => (
                                <option key={batch.batch_sk} value={batch.batch_sk}>
                                    {batch.batch_name}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Document Management Section */}
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
                                onClick={() => {
                                    const newDocs = formData.documents.filter((_, i) => i !== index);
                                    setFormData(prev => ({
                                        ...prev,
                                        documents: newDocs
                                    }));
                                }}
                                className="text-red-600 hover:text-red-900"
                            >
                                Remove
                            </button>
                        </div>
                    ))}
                    <button
                        type="button"
                        onClick={() => setFormData(prev => ({
                            ...prev,
                            documents: [...prev.documents, { document_sk: '', blob_link: '' }]
                        }))}
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
                        {loading ? 'Saving...' : 'Save Package'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default PackageManagement;