import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getSubscriptionInfo, getApiUsage } from '../../services/api';

const Dashboard = () => {
    const { user } = useAuth();
    const [subscription, setSubscription] = useState(null);
    const [usage, setUsage] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadDashboardData = async () => {
            try {
                const [subInfo, usageInfo] = await Promise.all([
                    getSubscriptionInfo(),
                    getApiUsage()
                ]);
                setSubscription(subInfo);
                setUsage(usageInfo);
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            } finally {
                setLoading(false);
            }
        };

        loadDashboardData();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
            
            {/* Subscription Info */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">Current Subscription</h2>
                {subscription && (
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <p className="text-gray-600">Plan</p>
                            <p className="font-medium">{subscription.tier_name}</p>
                        </div>
                        <div>
                            <p className="text-gray-600">Request Limit</p>
                            <p className="font-medium">{subscription.request_limit.toLocaleString()}</p>
                        </div>
                        <div>
                            <p className="text-gray-600">Used Requests</p>
                            <p className="font-medium">{usage?.total_requests.toLocaleString() || 0}</p>
                        </div>
                        <div>
                            <p className="text-gray-600">Remaining Requests</p>
                            <p className="font-medium">
                                {(subscription.request_limit - (usage?.total_requests || 0)).toLocaleString()}
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Usage Graph */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">API Usage</h2>
                {/* Add a graph component here */}
            </div>
        </div>
    );
};

export default Dashboard;