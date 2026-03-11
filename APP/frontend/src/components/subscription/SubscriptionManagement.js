import React, { useState, useEffect } from 'react';
import { getSubscriptionTiers, getCurrentUsage, upgradeSubscription } from '../../services/subscription';
import { format } from 'date-fns';

const SubscriptionManagement = () => {
    const [tiers, setTiers] = useState([]);
    const [usage, setUsage] = useState(null);
    const [loading, setLoading] = useState(true);
    const [upgrading, setUpgrading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [tiersData, usageData] = await Promise.all([
                    getSubscriptionTiers(),
                    getCurrentUsage()
                ]);
                
                // Add additional tier information
                const enhancedTiers = tiersData.map(tier => ({
                    ...tier,
                    features: [
                        `${tier.request_limit.toLocaleString()} requests per month`,
                        'Real-time API access',
                        'Technical support',
                        tier.tier_name === 'Gold' ? '24/7 Priority support' : 'Standard support',
                        tier.tier_name === 'Gold' ? 'Custom solutions' : 'Basic analytics'
                    ]
                }));

                setTiers(enhancedTiers);
                setUsage(usageData);
            } catch (err) {
                setError(err.response?.data?.error || 'Failed to load subscription data');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    const handleUpgrade = async (tierId) => {
        setUpgrading(true);
        setError(null);

        try {
            await upgradeSubscription(tierId);
            // Reload usage data after upgrade
            const usageData = await getCurrentUsage();
            setUsage(usageData);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to upgrade subscription');
        } finally {
            setUpgrading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100">
                <div className="flex flex-col items-center">
                    <svg className="animate-spin h-12 w-12 text-indigo-600 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p className="text-gray-600">Loading subscription data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Hero Section */}
                <div className="text-center mb-16">
                    <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                        <span className="block">Subscription Plans</span>
                        <span className="block text-indigo-600 mt-2">Choose the perfect plan for your API needs</span>
                    </h1>
                    <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
                        Scale your API usage with our flexible subscription tiers. Pay only for what you need.
                    </p>
                </div>

                {error && (
                    <div className="mb-8 rounded-lg bg-red-50 p-4 border-l-4 border-red-400">
                        <div className="flex">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div className="ml-3">
                                <p className="text-sm text-red-700">{error}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Current Usage Stats */}
                {usage && (
                    <div className="mb-16">
                        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
                            <div className="px-4 py-5 sm:p-6">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div className="p-6 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl text-white">
                                        <h3 className="text-lg font-medium opacity-90">Current Period</h3>
                                        <p className="mt-2 text-3xl font-bold">
                                            {format(new Date(usage.period_start), 'MMM d, yyyy')}
                                        </p>
                                    </div>
                                    <div className="p-6 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl text-white">
                                        <h3 className="text-lg font-medium opacity-90">API Requests</h3>
                                        <p className="mt-2 text-3xl font-bold">
                                            {usage.current_usage.toLocaleString()}
                                        </p>
                                    </div>
                                    <div className="p-6 bg-gradient-to-br from-violet-500 to-violet-600 rounded-xl text-white">
                                        <h3 className="text-lg font-medium opacity-90">Usage Period</h3>
                                        <p className="mt-2 text-3xl font-bold">30 Days Left</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Subscription Tiers */}
                <div className="grid gap-8 lg:grid-cols-3">
                    {tiers.map((tier) => (
                        <div key={tier.tier_id} 
                             className="relative bg-white rounded-2xl shadow-xl overflow-hidden transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
                            {tier.tier_name === 'Gold' && (
                                <div className="absolute top-0 right-0 -mt-3 mr-8">
                                    <span className="inline-flex items-center px-4 py-1 rounded-full text-sm font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
                                        Popular
                                    </span>
                                </div>
                            )}
                            <div className="p-8">
                                <h3 className="text-2xl font-bold text-gray-900 mb-4">
                                    {tier.tier_name}
                                </h3>
                                <p className="text-gray-500 mb-6">{tier.description}</p>
                                <div className="flex items-baseline mb-8">
                                    <span className="text-5xl font-extrabold text-gray-900">
                                        ${tier.pricing}
                                    </span>
                                    <span className="text-xl font-medium text-gray-500 ml-2">/mo</span>
                                </div>
                                <ul className="space-y-4 mb-8">
                                    {tier.features.map((feature, index) => (
                                        <li key={index} className="flex items-center">
                                            <svg className="w-5 h-5 text-indigo-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                            </svg>
                                            <span className="text-gray-600">{feature}</span>
                                        </li>
                                    ))}
                                </ul>
                                <button
                                    onClick={() => handleUpgrade(tier.tier_id)}
                                    disabled={upgrading}
                                    className="w-full py-4 px-6 rounded-xl text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {upgrading ? (
                                        <span className="flex items-center justify-center">
                                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Upgrading...
                                        </span>
                                    ) : (
                                        `Upgrade to ${tier.tier_name}`
                                    )}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default SubscriptionManagement;