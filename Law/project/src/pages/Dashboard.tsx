import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Calendar, MessageSquare, FileText, User } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="text-gray-600">Welcome back, {user?.full_name || 'User'}</div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Consultations', value: '12', icon: Calendar, color: 'bg-blue-500' },
          { label: 'Messages', value: '5', icon: MessageSquare, color: 'bg-green-500' },
          { label: 'Saved Articles', value: '8', icon: FileText, color: 'bg-purple-500' },
          { label: 'Profile Views', value: '24', icon: User, color: 'bg-yellow-500' },
        ].map((stat) => (
          <div key={stat.label} className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center space-x-4">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-gray-600">{stat.label}</p>
                <p className="text-2xl font-bold">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <section className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {[
            { title: 'Consultation Scheduled', time: '2 hours ago', type: 'consultation' },
            { title: 'New Message Received', time: '5 hours ago', type: 'message' },
            { title: 'Article Saved', time: '1 day ago', type: 'article' },
          ].map((activity, i) => (
            <div key={i} className="flex items-center space-x-4 py-3 border-b last:border-0">
              <div className="w-2 h-2 rounded-full bg-indigo-600" />
              <div className="flex-1">
                <p className="font-medium">{activity.title}</p>
                <p className="text-sm text-gray-500">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Upcoming Consultations */}
      <section className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-bold mb-4">Upcoming Consultations</h2>
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gray-200 rounded-full" />
                <div>
                  <p className="font-medium">John Doe</p>
                  <p className="text-sm text-gray-500">Family Law Consultation</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-medium">Tomorrow</p>
                <p className="text-sm text-gray-500">2:00 PM</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}