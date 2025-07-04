import React, { useState } from 'react';

/**
 * SystemHealth Component - Real-time system health monitoring
 * 
 * Displays health status of all system components including:
 * - WebSocket connection
 * - Message bus (Redis)
 * - Plugin status
 * - Memory system
 */
const SystemHealth = ({ healthData, isConnected, onRefresh }) => {
  const [expandedComponents, setExpandedComponents] = useState({});

  const toggleComponent = (componentName) => {
    setExpandedComponents(prev => ({
      ...prev,
      [componentName]: !prev[componentName]
    }));
  };

  const getStatusColor = (status) => {
    const statusColors = {
      operational: 'text-green-400',
      ready: 'text-green-400',
      active: 'text-green-400',
      degraded: 'text-yellow-400',
      error: 'text-red-400',
      disconnected: 'text-red-400',
      not_available: 'text-gray-400',
      unknown: 'text-gray-400'
    };
    return statusColors[status] || 'text-gray-400';
  };

  const getStatusIcon = (status) => {
    const statusIcons = {
      operational: '🟢',
      ready: '🟢',
      active: '🟢',
      degraded: '🟡',
      error: '🔴',
      disconnected: '🔴',
      not_available: '⚪',
      unknown: '⚪'
    };
    return statusIcons[status] || '⚪';
  };

  const getStatusBadge = (status) => {
    const statusColors = {
      operational: 'bg-green-900 text-green-200 border-green-700',
      ready: 'bg-green-900 text-green-200 border-green-700',
      active: 'bg-green-900 text-green-200 border-green-700',
      degraded: 'bg-yellow-900 text-yellow-200 border-yellow-700',
      error: 'bg-red-900 text-red-200 border-red-700',
      disconnected: 'bg-red-900 text-red-200 border-red-700',
      not_available: 'bg-gray-900 text-gray-200 border-gray-700',
      unknown: 'bg-gray-900 text-gray-200 border-gray-700'
    };
    return statusColors[status] || 'bg-gray-900 text-gray-200 border-gray-700';
  };

  const formatComponentName = (name) => {
    return name.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const renderComponentDetails = (componentName, componentData) => {
    if (typeof componentData === 'string') {
      return (
        <div className="mt-2 p-3 bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-300">Status: {componentData}</p>
        </div>
      );
    }

    if (typeof componentData === 'object' && componentData !== null) {
      return (
        <div className="mt-2 p-3 bg-gray-700 rounded-lg">
          <div className="space-y-2">
            {Object.entries(componentData).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center">
                <span className="text-sm text-gray-400">{formatComponentName(key)}:</span>
                <span className={`text-sm font-medium ${getStatusColor(value)}`}>
                  {getStatusIcon(value)} {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return null;
  };

  const components = healthData.components || {};
  const overallStatus = healthData.status || 'unknown';

  return (
    <div className="p-6 space-y-6">
      {/* Overall Status Card */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white mb-2">Overall System Status</h3>
            <div className="flex items-center space-x-3">
              <span className={`text-2xl ${getStatusColor(overallStatus)}`}>
                {getStatusIcon(overallStatus)}
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusBadge(overallStatus)}`}>
                {overallStatus.toUpperCase()}
              </span>
            </div>
          </div>
          <button
            onClick={onRefresh}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Refresh Status
          </button>
        </div>
      </div>

      {/* Connection Status */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-bold text-white mb-4">Connection Status</h3>
        <div className="flex items-center space-x-3">
          <span className={`text-xl ${getStatusColor(isConnected ? 'operational' : 'disconnected')}`}>
            {getStatusIcon(isConnected ? 'operational' : 'disconnected')}
          </span>
          <span className="text-white font-medium">
            WebSocket: {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Component Status */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-bold text-white mb-4">Component Status</h3>
        <div className="space-y-3">
          {Object.entries(components).map(([componentName, componentData]) => (
            <div key={componentName} className="border border-gray-700 rounded-lg">
              <button
                onClick={() => toggleComponent(componentName)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-700 transition-colors rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <span className={`text-lg ${getStatusColor(typeof componentData === 'string' ? componentData : 'unknown')}`}>
                    {getStatusIcon(typeof componentData === 'string' ? componentData : 'unknown')}
                  </span>
                  <span className="text-white font-medium">
                    {formatComponentName(componentName)}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusBadge(typeof componentData === 'string' ? componentData : 'unknown')}`}>
                    {typeof componentData === 'string' ? componentData : 'Multiple'}
                  </span>
                  <span className="text-gray-400">
                    {expandedComponents[componentName] ? '▼' : '▶'}
                  </span>
                </div>
              </button>
              
              {expandedComponents[componentName] && renderComponentDetails(componentName, componentData)}
            </div>
          ))}
          
          {Object.keys(components).length === 0 && (
            <div className="text-center py-8 text-gray-400">
              <p>No component data available</p>
              <p className="text-sm mt-2">Try refreshing the status</p>
            </div>
          )}
        </div>
      </div>

      {/* Health Metrics */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-bold text-white mb-4">System Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-400 mb-2">Last Update</h4>
            <p className="text-white">
              {new Date().toLocaleString()}
            </p>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-400 mb-2">Components Monitored</h4>
            <p className="text-white">
              {Object.keys(components).length}
            </p>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-400 mb-2">Operational Components</h4>
            <p className="text-green-400">
              {Object.entries(components).filter(([_, status]) => 
                status === 'operational' || status === 'ready' || status === 'active'
              ).length}
            </p>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-400 mb-2">Issues Detected</h4>
            <p className="text-red-400">
              {Object.entries(components).filter(([_, status]) => 
                status === 'error' || status === 'disconnected'
              ).length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealth;