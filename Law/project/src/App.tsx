import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import News from './pages/News';
import Stories from './pages/Stories';
import LawyerSearch from './pages/LawyerSearch';
import LegalResources from './pages/LegalResources';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import { AuthProvider } from './contexts/AuthContext';
import SupabaseConnectionPrompt from './components/SupabaseConnectionPrompt';
import { isSupabaseConnected } from './lib/supabase';

export default function App() {
  if (!isSupabaseConnected()) {
    return <SupabaseConnectionPrompt />;
  }

  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Navbar />
          <main className="flex-grow container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/news" element={<News />} />
              <Route path="/stories" element={<Stories />} />
              <Route path="/login" element={<Login />} />
              <Route path="/lawyers" element={<LawyerSearch />} />
              <Route path="/resources" element={<LegalResources />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </main>
          <Footer />
          <Toaster position="top-right" />
        </div>
      </Router>
    </AuthProvider>
  );
}