import React from 'react';
import { Scale } from 'lucide-react';

export default function SupabaseConnectionPrompt() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center p-8 max-w-md">
        <Scale className="h-12 w-12 text-indigo-600 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Connect to Supabase</h1>
        <p className="text-gray-600 mb-6">
          To use LegalConnect, please click the "Connect to Supabase" button in the top right corner to set up your database connection.
        </p>
        <div className="animate-bounce text-indigo-600">
          <span className="text-2xl">↗️</span>
        </div>
      </div>
    </div>
  );
}