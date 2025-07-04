import React, { useState, useEffect } from 'react';
import SystemHealth from './SystemHealth';
import MissionDisplay from './MissionDisplay';

/**
 * Dashboard Component - System monitoring and management interface
 * 
 * Provides real-time system health monitoring, mission management,
 * and conversation analytics for the Riker Conversation Engine
 */
const Dashboard = ({ systemHealth, conversations, isConnected }) => {
  const [activeTab, setActiveTab] = useState('health');
  const [healthData, setHealthData] = useState({});
  const [refreshInterval, setRefreshInterval] = useState(null);

  // Poll system health data
  useEffect(() => {
    const fetchHealthData = async () => {
      try {
        const response = await fetch('http://localhost:8000/health');
        const data = await response.json();
        setHealthData(data);
      } catch (error) {
        console.error('Error fetching health data:', error);
        setHealthData({
          status: 'error',
          components: { error: 'Failed to fetch health data' }
        });
      }
    };

    // Initial fetch
    fetchHealthData();

    // Set up polling interval
    const interval = setInterval(fetchHealthData, 30000); // 30 seconds
    setRefreshInterval(interval);

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, []);

  const getTabClass = (tab) => {
    return activeTab === tab
      ? 'bg-blue-600 text-white border-blue-600'
      : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border-gray-600';
  };

  const getStatusBadge = (status) => {
    const statusColors = {
      operational: 'bg-green-900 text-green-200',
      degraded: 'bg-yellow-900 text-yellow-200',
      error: 'bg-red-900 text-red-200',
      disconnected: 'bg-gray-900 text-gray-200'
    };
    return statusColors[status] || 'bg-gray-900 text-gray-200';
  };

  const getTotalMessages = () => {
    return Object.values(conversations).reduce((total, conv) => 
      total + (conv.messages?.length || 0), 0
    );
  };

  const getActiveConversations = () => {
    return Object.keys(conversations).length;
  };

  const manualRefresh = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setHealthData(data);
    } catch (error) {
      console.error('Error refreshing health data:', error);
    }
  };

  return (
    <div className="dashboard h-full bg-gray-900 text-white">
      {/* Dashboard Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-blue-400">System Dashboard</h2>
            <p className="text-gray-400 text-sm mt-1">
              Monitor system health and manage conversations
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(healthData.status)}`}>
              {healthData.status || 'Unknown'}
            </span>
            <button 
              onClick={manualRefresh}
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-lg text-sm font-medium transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-gray-800 border-b border-gray-700 px-6">
        <nav className="flex space-x-4">
          <button
            onClick={() => setActiveTab('health')}
            className={`px-4 py-3 border-b-2 font-medium transition-colors ${getTabClass('health')}`}
          >
            System Health
          </button>
          <button
            onClick={() => setActiveTab('missions')}
            className={`px-4 py-3 border-b-2 font-medium transition-colors ${getTabClass('missions')}`}
          >
            Missions
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-3 border-b-2 font-medium transition-colors ${getTabClass('analytics')}`}
          >
            Analytics
          </button>
        </nav>
      </div>

      {/* Dashboard Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'health' && (
          <SystemHealth 
            healthData={healthData} 
            isConnected={isConnected}
            onRefresh={manualRefresh}
          />
        )}
        
        {activeTab === 'missions' && (
          <MissionDisplay 
            isConnected={isConnected}
          />
        )}
        
        {activeTab === 'analytics' && (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Analytics Cards */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Active Conversations</h3>
                <p className="text-2xl font-bold text-blue-400">{getActiveConversations()}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Total Messages</h3>
                <p className="text-2xl font-bold text-green-400">{getTotalMessages()}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Connection Status</h3>
                <p className="text-2xl font-bold text-yellow-400">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-sm font-medium text-gray-400 mb-2">System Status</h3>
                <p className="text-2xl font-bold text-purple-400">
                  {healthData.status || 'Unknown'}
                </p>
              </div>
            </div>

            {/* Conversation Analytics */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-bold text-white mb-4">Conversation Analytics</h3>
              <div className="space-y-4">
                {Object.entries(conversations).map(([conversationId, conversation]) => (
                  <div key={conversationId} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                    <div>
                      <p className="font-medium text-white">Conversation {conversationId}</p>
                      <p className="text-sm text-gray-400">
                        {conversation.messages?.length || 0} messages
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-400">
                        Last activity: {conversation.lastActivity || 'N/A'}
                      </p>
                    </div>
                  </div>
                ))}
                {Object.keys(conversations).length === 0 && (
                  <p className="text-gray-400 text-center py-8">No conversations yet</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;