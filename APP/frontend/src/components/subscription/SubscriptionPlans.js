 
import { useAuth } from '../../context/AuthContext';
import { upgradeSubscription } from '../../services/api';

const SubscriptionPlans = () => {
    const { user } = useAuth();
    
    const plans = [
        {
            id: 'SILVER',
            name: 'Silver',
            requests: 10000,
            price: 29.99,
            features: [
                '10,000 API requests per month',
                'Basic support',
                'Standard API access'
            ]
        },
        {
            id: 'BRONZE',
            name: 'Bronze',
            requests: 500000,
            price: 99.99,
            features: [
                '500,000 API requests per month',
                'Priority support',
                'Enhanced API access'
            ]
        },
        {
            id: 'GOLD',
            name: 'Gold',
            requests: 1000000,
            price: 299.99,
            features: [
                '1,000,000 API requests per month',
                '24/7 Premium support',
                'Full API access'
            ]
        }
    ];

    const handleUpgrade = async (planId) => {
        try {
            await upgradeSubscription(planId);
            // Handle successful upgrade
            window.location.reload();
        } catch (error) {
            console.error('Error upgrading subscription:', error);
        }
    };

    return (
        <div className="py-12 bg-gray-100">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center">
                    <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                        Subscription Plans
                    </h2>
                    <p className="mt-4 text-xl text-gray-600">
                        Choose the perfect plan for your needs
                    </p>
                </div>

                <div className="mt-12 space-y-4 sm:mt-16 sm:space-y-0 sm:grid sm:grid-cols-3 sm:gap-6 lg:max-w-4xl lg:mx-auto xl:max-w-none xl:mx-0">
                    {plans.map((plan) => (
                        <div
                            key={plan.id}
                            className="bg-white border border-gray-200 rounded-lg shadow-sm divide-y divide-gray-200"
                        >
                            <div className="p-6">
                                <h3 className="text-xl font-semibold text-gray-900">
                                    {plan.name}
                                </h3>
                                <p className="mt-4 text-gray-500">
                                    {plan.requests.toLocaleString()} requests per month
                                </p>
                                <p className="mt-8">
                                    <span className="text-4xl font-extrabold text-gray-900">
                                        ${plan.price}
                                    </span>
                                    <span className="text-base font-medium text-gray-500">
                                        /mo
                                    </span>
                                </p>
                                <button
                                    onClick={() => handleUpgrade(plan.id)}
                                    className="mt-8 block w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded"
                                >
                                    Upgrade to {plan.name}
                                </button>
                            </div>
                            <div className="px-6 pt-6 pb-8">
                                <h4 className="text-sm font-medium text-gray-900 tracking-wide">
                                    What's included
                                </h4>
                                <ul className="mt-6 space-y-4">
                                    {plan.features.map((feature, index) => (
                                        <li key={index} className="flex space-x-3">
                                            <svg
                                                className="flex-shrink-0 h-5 w-5 text-green-500"
                                                xmlns="http://www.w3.org/2000/svg"
                                                viewBox="0 0 20 20"
                                                fill="currentColor"
                                            >
                                                <path
                                                    fillRule="evenodd"
                                                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                                    clipRule="evenodd"
                                                />
                                            </svg>
                                            <span className="text-sm text-gray-500">
                                                {feature}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default SubscriptionPlans;