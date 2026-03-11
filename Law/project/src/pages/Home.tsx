import React from 'react';
import { Link } from 'react-router-dom';
import { Search, Users, MessageSquare, Scale } from 'lucide-react';
import LegalChat from '../components/LegalChat';

export default function Home() {
  return (
    <div className="space-y-16">
      {/* Hero Section with Centered Chat */}
      <section className="max-w-4xl mx-auto text-center space-y-8">
        <h1 className="text-5xl font-bold text-gray-900">
          Legal Help Made Simple
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Get instant answers to your legal questions with our AI-powered assistant. Connect with experienced lawyers and access comprehensive legal resources.
        </p>
        <LegalChat />
        <div className="flex justify-center gap-4">
          <Link
            to="/lawyers"
            className="bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700"
          >
            Find a Lawyer
          </Link>
          <Link
            to="/resources"
            className="bg-white text-indigo-600 px-6 py-3 rounded-md border border-indigo-600 hover:bg-indigo-50"
          >
            Browse Resources
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="grid md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <Search className="h-12 w-12 text-indigo-600 mb-4" />
          <h3 className="text-xl font-semibold mb-2">Find the Right Lawyer</h3>
          <p className="text-gray-600">
            Search and filter through our network of verified lawyers based on expertise,
            location, and reviews.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <MessageSquare className="h-12 w-12 text-indigo-600 mb-4" />
          <h3 className="text-xl font-semibold mb-2">Get Legal Advice</h3>
          <p className="text-gray-600">
            Connect with lawyers through our platform for consultations and legal guidance.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <Scale className="h-12 w-12 text-indigo-600 mb-4" />
          <h3 className="text-xl font-semibold mb-2">Legal Resources</h3>
          <p className="text-gray-600">
            Access our comprehensive library of legal information and educational content.
          </p>
        </div>
      </section>

      {/* Featured Lawyers Section */}
      <section className="bg-white p-8 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Featured Lawyers</h2>
          <Link to="/lawyers" className="text-indigo-600 hover:text-indigo-700">
            View all →
          </Link>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              name: 'Sarah Johnson',
              specialty: 'Family Law',
              image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=150&h=150',
              rating: 5
            },
            {
              name: 'Michael Chen',
              specialty: 'Corporate Law',
              image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=150&h=150',
              rating: 5
            },
            {
              name: 'Emily Rodriguez',
              specialty: 'Immigration Law',
              image: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&q=80&w=150&h=150',
              rating: 5
            }
          ].map((lawyer) => (
            <div key={lawyer.name} className="border rounded-lg p-4">
              <img
                src={lawyer.image}
                alt={lawyer.name}
                className="w-20 h-20 rounded-full mb-4 object-cover"
              />
              <h3 className="font-semibold">{lawyer.name}</h3>
              <p className="text-gray-600">{lawyer.specialty}</p>
              <div className="mt-2 text-yellow-500">{'★'.repeat(lawyer.rating)}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}