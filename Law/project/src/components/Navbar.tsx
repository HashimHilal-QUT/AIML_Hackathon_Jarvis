import React from 'react';
import { Link } from 'react-router-dom';
import { Scale, Search, Book, User, Newspaper, BookOpen } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Navbar() {
  const { user, signOut } = useAuth();

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Scale className="h-8 w-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-900">LegalConnect</span>
          </Link>

          <div className="hidden md:flex items-center space-x-8">
            <Link to="/news" className="flex items-center space-x-1 text-gray-600 hover:text-indigo-600">
              <Newspaper className="h-4 w-4" />
              <span>News</span>
            </Link>
            <Link to="/stories" className="flex items-center space-x-1 text-gray-600 hover:text-indigo-600">
              <BookOpen className="h-4 w-4" />
              <span>Stories</span>
            </Link>
            <Link to="/lawyers" className="flex items-center space-x-1 text-gray-600 hover:text-indigo-600">
              <Search className="h-4 w-4" />
              <span>Find Lawyers</span>
            </Link>
            <Link to="/resources" className="flex items-center space-x-1 text-gray-600 hover:text-indigo-600">
              <Book className="h-4 w-4" />
              <span>Legal Resources</span>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Link to="/dashboard" className="flex items-center space-x-1 text-gray-600 hover:text-indigo-600">
                  <User className="h-4 w-4" />
                  <span>Dashboard</span>
                </Link>
                <button
                  onClick={() => signOut()}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}