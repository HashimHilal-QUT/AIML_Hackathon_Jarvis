 
import { Link } from 'react-router-dom';

const Home = () => {
    return (
        <div className="min-h-screen bg-gray-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="text-center">
                    <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl">
                        API Platform
                    </h1>
                    <p className="mt-3 text-xl text-gray-500">
                        Manage your API subscriptions and packages
                    </p>
                    <div className="mt-8 space-y-4 sm:space-y-0 sm:space-x-4">
                        <Link
                            to="/subscriptions"
                            className="inline-block bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700"
                        >
                            View Subscriptions
                        </Link>
                        <Link
                            to="/packages"
                            className="inline-block bg-white text-indigo-600 px-6 py-3 rounded-md border border-indigo-600 hover:bg-indigo-50"
                        >
                            Manage Packages
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;