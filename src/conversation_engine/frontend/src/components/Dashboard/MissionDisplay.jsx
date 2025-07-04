import React, { useState, useEffect } from 'react';

/**
 * MissionDisplay Component - Mission management interface
 * 
 * Displays and manages Away Missions including:
 * - Mission list and status
 * - Mission creation interface
 * - Mission progress tracking
 * - Integration with GitHub Issues
 */
const MissionDisplay = ({ isConnected }) => {
  const [missions, setMissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateMission, setShowCreateMission] = useState(false);
  const [newMission, setNewMission] = useState({
    title: '',
    description: '',
    priority: 'medium',
    assignee: ''
  });

  // Mock mission data - in real implementation, this would come from GitHub Integration plugin
  const mockMissions = [
    {
      id: '1',
      title: 'Config Manager Implementation',
      description: 'Implement configuration management plugin with YAML/JSON support',
      status: 'completed',
      priority: 'high',
      assignee: 'Claude',
      created_at: '2025-07-01T10:00:00Z',
      updated_at: '2025-07-02T15:30:00Z',
      progress: 100,
      labels: ['plugin', 'config', 'away-mission']
    },
    {
      id: '7',
      title: 'Conversation Engine Implementation',
      description: 'Central orchestrator for conversational AI development',
      status: 'in_progress',
      priority: 'high',
      assignee: 'Claude',
      created_at: '2025-07-02T14:00:00Z',
      updated_at: '2025-07-04T12:00:00Z',
      progress: 85,
      labels: ['ai', 'conversation', 'away-mission']
    },
    {
      id: '3',
      title: 'GitHub Integration Plugin',
      description: 'Seamless GitHub repository integration for mission management',
      status: 'open',
      priority: 'medium',
      assignee: 'Unassigned',
      created_at: '2025-07-01T09:00:00Z',
      updated_at: '2025-07-03T11:00:00Z',
      progress: 25,
      labels: ['plugin', 'github', 'integration']
    }
  ];

  useEffect(() => {
    // Simulate loading missions
    setLoading(true);
    setTimeout(() => {
      setMissions(mockMissions);
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusColor = (status) => {
    const statusColors = {
      open: 'text-blue-400',
      in_progress: 'text-yellow-400',
      completed: 'text-green-400',
      closed: 'text-gray-400',
      disbanded: 'text-red-400'
    };
    return statusColors[status] || 'text-gray-400';
  };

  const getStatusBadge = (status) => {
    const statusColors = {
      open: 'bg-blue-900 text-blue-200 border-blue-700',
      in_progress: 'bg-yellow-900 text-yellow-200 border-yellow-700',
      completed: 'bg-green-900 text-green-200 border-green-700',
      closed: 'bg-gray-900 text-gray-200 border-gray-700',
      disbanded: 'bg-red-900 text-red-200 border-red-700'
    };
    return statusColors[status] || 'bg-gray-900 text-gray-200 border-gray-700';
  };

  const getPriorityColor = (priority) => {
    const priorityColors = {
      high: 'text-red-400',
      medium: 'text-yellow-400',
      low: 'text-green-400'
    };
    return priorityColors[priority] || 'text-gray-400';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleCreateMission = async () => {
    if (!newMission.title.trim()) {
      setError('Mission title is required');
      return;
    }

    setLoading(true);
    try {
      // In real implementation, this would send to backend via WebSocket
      const mission = {
        id: Date.now().toString(),
        ...newMission,
        status: 'open',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        progress: 0,
        labels: ['away-mission']
      };

      setMissions(prev => [...prev, mission]);
      setNewMission({
        title: '',
        description: '',
        priority: 'medium',
        assignee: ''
      });
      setShowCreateMission(false);
      setError(null);
    } catch (error) {
      setError('Failed to create mission');
      console.error('Error creating mission:', error);
    } finally {
      setLoading(false);
    }
  };

  const getProgressBarColor = (progress) => {
    if (progress >= 80) return 'bg-green-500';
    if (progress >= 50) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">Away Missions</h3>
          <p className="text-gray-400 text-sm mt-1">
            Manage and track development missions
          </p>
        </div>
        <button
          onClick={() => setShowCreateMission(true)}
          disabled={!isConnected}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Create Mission
        </button>
      </div>

      {/* Mission Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Total Missions</h4>
          <p className="text-2xl font-bold text-white">{missions.length}</p>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h4 className="text-sm font-medium text-gray-400 mb-2">In Progress</h4>
          <p className="text-2xl font-bold text-yellow-400">
            {missions.filter(m => m.status === 'in_progress').length}
          </p>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Completed</h4>
          <p className="text-2xl font-bold text-green-400">
            {missions.filter(m => m.status === 'completed').length}
          </p>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Open</h4>
          <p className="text-2xl font-bold text-blue-400">
            {missions.filter(m => m.status === 'open').length}
          </p>
        </div>
      </div>

      {/* Mission List */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <h4 className="text-lg font-medium text-white">Mission List</h4>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading missions...</p>
          </div>
        ) : missions.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <p>No missions found</p>
            <p className="text-sm mt-2">Create your first mission to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {missions.map((mission) => (
              <div key={mission.id} className="p-4 hover:bg-gray-700 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h5 className="text-white font-medium">{mission.title}</h5>
                      <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusBadge(mission.status)}`}>
                        {mission.status.replace('_', ' ')}
                      </span>
                      <span className={`text-xs font-medium ${getPriorityColor(mission.priority)}`}>
                        {mission.priority.toUpperCase()}
                      </span>
                    </div>
                    
                    <p className="text-gray-400 text-sm mb-3">{mission.description}</p>
                    
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>#{mission.id}</span>
                      <span>Created: {formatDate(mission.created_at)}</span>
                      <span>Updated: {formatDate(mission.updated_at)}</span>
                      <span>Assignee: {mission.assignee || 'Unassigned'}</span>
                    </div>
                    
                    {mission.labels && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {mission.labels.map((label) => (
                          <span key={label} className="bg-gray-700 text-gray-300 px-2 py-1 rounded text-xs">
                            {label}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="ml-4 text-right">
                    <div className="text-sm text-gray-400 mb-1">Progress</div>
                    <div className="w-24 bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getProgressBarColor(mission.progress)}`}
                        style={{ width: `${mission.progress}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{mission.progress}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Mission Modal */}
      {showCreateMission && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-700">
            <h3 className="text-lg font-bold text-white mb-4">Create New Mission</h3>
            
            {error && (
              <div className="bg-red-900 text-red-200 p-3 rounded-lg mb-4">
                {error}
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Mission Title
                </label>
                <input
                  type="text"
                  value={newMission.title}
                  onChange={(e) => setNewMission(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  placeholder="Enter mission title"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Description
                </label>
                <textarea
                  value={newMission.description}
                  onChange={(e) => setNewMission(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  rows="3"
                  placeholder="Enter mission description"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Priority
                </label>
                <select
                  value={newMission.priority}
                  onChange={(e) => setNewMission(prev => ({ ...prev, priority: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Assignee
                </label>
                <input
                  type="text"
                  value={newMission.assignee}
                  onChange={(e) => setNewMission(prev => ({ ...prev, assignee: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  placeholder="Enter assignee name"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateMission(false);
                  setError(null);
                }}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateMission}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded-lg text-white font-medium transition-colors"
              >
                {loading ? 'Creating...' : 'Create Mission'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MissionDisplay;