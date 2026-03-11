import React from 'react';
import { Book, FileText, Search } from 'lucide-react';

export default function LegalResources() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Legal Resources</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Access our comprehensive library of legal information, guides, and educational content.
        </p>
      </div>

      {/* Search */}
      <div className="max-w-2xl mx-auto">
        <div className="relative">
          <input
            type="text"
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Search resources..."
          />
          <Search className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
        </div>
      </div>

      {/* Categories */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          { title: 'Family Law', icon: Book, count: 45 },
          { title: 'Criminal Law', icon: Book, count: 32 },
          { title: 'Corporate Law', icon: Book, count: 28 },
          { title: 'Real Estate', icon: Book, count: 37 },
          { title: 'Immigration', icon: Book, count: 23 },
          { title: 'Employment', icon: Book, count: 41 },
        ].map((category) => (
          <div key={category.title} className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <div className="flex items-center space-x-3 mb-4">
              <category.icon className="h-6 w-6 text-indigo-600" />
              <h3 className="text-lg font-semibold">{category.title}</h3>
            </div>
            <p className="text-gray-600 mb-4">
              {category.count} articles
            </p>
            <button className="text-indigo-600 hover:text-indigo-700 font-medium">
              Browse Articles →
            </button>
          </div>
        ))}
      </div>

      {/* Recent Articles */}
      <section>
        <h2 className="text-2xl font-bold mb-6">Recent Articles</h2>
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-start space-x-4">
                <FileText className="h-6 w-6 text-indigo-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold text-lg mb-2">
                    Understanding Your Rights in Family Court
                  </h3>
                  <p className="text-gray-600 mb-4">
                    A comprehensive guide to family court proceedings, your rights, and what to expect during the process.
                  </p>
                  <div className="flex items-center text-sm text-gray-500">
                    <span>10 min read</span>
                    <span className="mx-2">•</span>
                    <span>Family Law</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}