import React from 'react';
import { Search } from 'lucide-react';

export default function LawyerSearch() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Find a Lawyer</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Connect with experienced lawyers in your area. Use the filters below to find the right legal expert for your needs.
        </p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <div className="relative">
              <input
                type="text"
                id="search"
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Search by name, expertise, or location"
              />
              <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          <div className="w-full md:w-48">
            <label htmlFor="expertise" className="block text-sm font-medium text-gray-700 mb-1">
              Expertise
            </label>
            <select
              id="expertise"
              className="w-full py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Areas</option>
              <option value="family">Family Law</option>
              <option value="criminal">Criminal Law</option>
              <option value="corporate">Corporate Law</option>
              <option value="real-estate">Real Estate</option>
            </select>
          </div>

          <div className="w-full md:w-48">
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <select
              id="location"
              className="w-full py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Locations</option>
              <option value="ny">New York</option>
              <option value="ca">California</option>
              <option value="tx">Texas</option>
              <option value="fl">Florida</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results - Placeholder */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-start space-x-4">
              <div className="w-16 h-16 bg-gray-200 rounded-full flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-lg">John Doe</h3>
                <p className="text-gray-600">Family Law</p>
                <div className="text-yellow-400 text-sm">★★★★★</div>
                <p className="text-sm text-gray-500 mt-2">15 years experience</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t">
              <button className="w-full bg-indigo-600 text-white py-2 rounded-md hover:bg-indigo-700">
                View Profile
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}