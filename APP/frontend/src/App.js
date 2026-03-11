import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Navigation from './components/common/Navigation';
import Home from './components/Home';
import Register from './components/auth/Register';
import Login from './components/auth/Login';
import SubscriptionManagement from './components/subscription/SubscriptionManagement';
import PackageManagement from './components/package/PackageManagement';
import AdminDashboard from './components/admin/AdminDashboard';

// Protected Route component
const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();
    
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }
    
    if (!user) {
        return <Navigate to="/login" />;
    }
    
    return children;
};

function App() {
    const { loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    return (
        <Router>
            <div className="min-h-screen bg-gray-100">
                <Routes>
                    {/* Public routes */}
                    <Route path="/register" element={<Register />} />
                    <Route path="/login" element={<Login />} />
                    
                    {/* Protected routes */}
                    <Route path="/" element={
                        <ProtectedRoute>
                            <Navigation />
                            <Home />
                        </ProtectedRoute>
                    } />
                    <Route path="/subscriptions" element={
                        <ProtectedRoute>
                            <Navigation />
                            <SubscriptionManagement />
                        </ProtectedRoute>
                    } />
                    <Route path="/packages" element={
                        <ProtectedRoute>
                            <Navigation />
                            <PackageManagement />
                        </ProtectedRoute>
                    } />
                    <Route path="/admin" element={
                        <ProtectedRoute>
                            <Navigation />
                            <AdminDashboard />
                        </ProtectedRoute>
                    } />
                    
                    {/* Redirect to register page for unknown routes */}
                    <Route path="*" element={<Navigate to="/register" replace />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;