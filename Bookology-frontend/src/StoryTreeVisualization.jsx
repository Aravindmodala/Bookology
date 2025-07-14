import React, { useState, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { API_BASE_URL, API_ENDPOINTS } from './config';
import { useAuth } from './AuthContext';

// Custom Chapter Node Component
const ChapterNode = ({ data, isConnectable }) => {
  const { chapter_number, title, content, branch_name, is_main_branch, word_count } = data;
  
  return (
    <div 
      className={`px-4 py-3 shadow-xl rounded-xl border-2 min-w-[220px] max-w-[320px] cursor-pointer transition-all duration-200 hover:scale-105 hover:shadow-2xl ${
        is_main_branch 
          ? 'bg-gradient-to-br from-blue-900 to-blue-800 border-blue-400 hover:border-blue-300' 
          : 'bg-gradient-to-br from-purple-900 to-purple-800 border-purple-400 hover:border-purple-300'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg ${
          is_main_branch ? 'bg-gradient-to-br from-blue-500 to-blue-600' : 'bg-gradient-to-br from-purple-500 to-purple-600'
        }`}>
          {chapter_number}
        </div>
        <div className={`text-xs px-2 py-1 rounded-full ${
          is_main_branch ? 'bg-blue-800/50 text-blue-200' : 'bg-purple-800/50 text-purple-200'
        }`}>
          {branch_name}
        </div>
      </div>
      
      <div className="text-white">
        <h4 className="font-semibold text-sm mb-2 line-clamp-2 leading-tight">
          {title}
        </h4>
        <p className="text-xs text-gray-300 line-clamp-3 leading-relaxed mb-3">
          {content?.substring(0, 150)}...
        </p>
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>{word_count} words</span>
          <span className="opacity-70">📖</span>
        </div>
      </div>
    </div>
  );
};

// Custom Choice Edge Component
const ChoiceEdge = ({ 
  id, 
  sourceX, 
  sourceY, 
  targetX, 
  targetY, 
  sourcePosition, 
  targetPosition,
  data 
}) => {
  const { choice_title, is_selected, story_impact } = data;
  
  // Create a curved path for better visual appeal
  const edgePath = `M${sourceX},${sourceY} Q${(sourceX + targetX) / 2},${sourceY - 60} ${targetX},${targetY}`;
  
  // Get colors based on selection and impact
  const getEdgeColor = () => {
    if (is_selected) return '#10b981'; // Green for selected
    switch (story_impact) {
      case 'high': return '#ef4444'; // Red for high impact
      case 'medium': return '#f59e0b'; // Orange for medium impact
      case 'low': return '#6b7280'; // Gray for low impact
      default: return '#6b7280';
    }
  };
  
  return (
    <>
      <path
        id={id}
        style={{
          stroke: getEdgeColor(),
          strokeWidth: is_selected ? 4 : 3,
          fill: 'none',
          strokeDasharray: is_selected ? '0' : '8,4',
          filter: is_selected ? 'drop-shadow(0 0 6px rgba(16, 185, 129, 0.6))' : 'none',
          cursor: 'pointer',
        }}
        className="react-flow__edge-path hover:opacity-80 transition-opacity"
        d={edgePath}
      />
      <text>
        <textPath href={`#${id}`} startOffset="50%" textAnchor="middle">
          <tspan 
            className={`text-xs font-medium fill-current ${
              is_selected ? 'text-green-300' : 'text-gray-300'
            }`}
            style={{
              textShadow: is_selected ? '0 0 4px rgba(16, 185, 129, 0.8)' : '0 0 2px rgba(0, 0, 0, 0.8)',
            }}
          >
            {choice_title}
          </tspan>
        </textPath>
      </text>
      
      {/* Add impact indicator */}
      {!is_selected && (
        <circle
          cx={(sourceX + targetX) / 2}
          cy={sourceY - 60}
          r="3"
          fill={getEdgeColor()}
          className="opacity-70"
        />
      )}
    </>
  );
};

// Node types
const nodeTypes = {
  chapter: ChapterNode,
};

// Edge types
const edgeTypes = {
  choice: ChoiceEdge,
};

const StoryTreeVisualization = ({ storyId, onClose, onNodeClick, onEdgeClick }) => {
  const { session } = useAuth();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [treeData, setTreeData] = useState(null);

  // Fetch tree data from backend
  const fetchTreeData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const token = session?.access_token;
      if (!token) {
        throw new Error('No authentication token found. Please log in.');
      }

      const response = await fetch(
        `${API_BASE_URL}${API_ENDPOINTS.GET_STORY_TREE.replace('{story_id}', storyId)}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setTreeData(data.tree);
        processTreeData(data.tree);
      } else {
        throw new Error(data.detail || 'Failed to fetch tree data');
      }
    } catch (err) {
      console.error('❌ Error fetching tree data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Process tree data into React Flow format
  const processTreeData = (tree) => {
    const processedNodes = tree.nodes.map(node => ({
      id: node.id,
      type: 'chapter',
      position: node.position,
      data: {
        chapter_number: node.chapter_number,
        title: node.title,
        content: node.content,
        branch_name: node.branch_name,
        is_main_branch: node.is_main_branch,
        word_count: node.word_count,
        chapter_id: node.chapter_id,
        branch_id: node.branch_id,
      },
    }));

    const processedEdges = tree.edges.map(edge => ({
      id: edge.id,
      type: 'choice',
      source: edge.source,
      target: edge.target,
      data: {
        choice_title: edge.choice_title,
        choice_description: edge.choice_description,
        is_selected: edge.is_selected,
        story_impact: edge.story_impact,
        choice_id: edge.choice_id,
      },
    }));

    setNodes(processedNodes);
    setEdges(processedEdges);
  };

  // Handle node click
  const onNodeClickHandler = useCallback((event, node) => {
    console.log('🎯 Node clicked:', node);
    if (onNodeClick) {
      onNodeClick(node.data);
    }
  }, [onNodeClick]);

  // Handle edge click
  const onEdgeClickHandler = useCallback((event, edge) => {
    console.log('🎯 Edge clicked:', edge);
    if (onEdgeClick) {
      onEdgeClick(edge.data);
    } else {
      // Default behavior: show choice info
      const choiceInfo = `Choice: ${edge.data.choice_title}\n\nDescription: ${edge.data.choice_description}\nImpact: ${edge.data.story_impact}\nSelected: ${edge.data.is_selected ? 'Yes' : 'No'}`;
      alert(choiceInfo);
    }
  }, [onEdgeClick]);

  useEffect(() => {
    if (storyId && session?.access_token) {
      fetchTreeData();
    }
  }, [storyId, session?.access_token]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-gray-900 rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="text-white text-lg mb-4">🌳 Loading Story Tree...</div>
            <div className="w-full bg-gray-800 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full animate-pulse w-2/3"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-gray-900 rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="text-red-400 text-lg mb-4">❌ Error Loading Tree</div>
            <p className="text-gray-300 mb-4">{error}</p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={fetchTreeData}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              >
                Retry
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50">
      <div className="w-full h-full flex flex-col">
        {/* Header */}
        <div className="bg-gray-900 border-b border-gray-800 p-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">
              🌳 {treeData?.story?.title || 'Story Tree'}
            </h2>
            <p className="text-gray-400 text-sm">
              {treeData?.metadata?.total_branches} branches • {treeData?.metadata?.total_chapters} chapters • {treeData?.metadata?.total_choices} choices
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ✕
          </button>
        </div>

        {/* React Flow Container */}
        <div className="flex-1 bg-gray-950">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClickHandler}
            onEdgeClick={onEdgeClickHandler}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            fitViewOptions={{
              padding: 50,
              includeHiddenNodes: false,
            }}
            defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
            minZoom={0.1}
            maxZoom={2}
            deleteKeyCode={null} // Disable delete key
            multiSelectionKeyCode={null} // Disable multi-selection
          >
            <Controls 
              position="top-right"
              showZoom={true}
              showFitView={true}
              showInteractive={false}
            />
            <MiniMap 
              position="bottom-right"
              nodeColor={(node) => node.data.is_main_branch ? '#3b82f6' : '#8b5cf6'}
              maskColor="rgba(0, 0, 0, 0.8)"
              style={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
              }}
            />
            <Background 
              color="#374151" 
              gap={20} 
              size={1}
              variant="dots"
            />
            
            {/* Legend Panel */}
            <Panel position="top-left" className="bg-gray-900/90 backdrop-blur-sm border border-gray-700 rounded-lg p-4 shadow-xl">
              <div className="text-white text-sm">
                <div className="font-semibold mb-3 text-gray-200">🗺️ Legend</div>
                
                {/* Chapter Types */}
                <div className="mb-3">
                  <div className="text-xs font-medium text-gray-400 mb-1">Chapters</div>
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-4 h-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full"></div>
                    <span className="text-gray-300 text-xs">Main Branch</span>
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-4 h-4 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full"></div>
                    <span className="text-gray-300 text-xs">Alternative Branch</span>
                  </div>
                </div>
                
                {/* Choice Types */}
                <div>
                  <div className="text-xs font-medium text-gray-400 mb-1">Choices</div>
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-4 h-1 bg-green-500 shadow-sm"></div>
                    <span className="text-gray-300 text-xs">Selected Path</span>
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-4 h-1 bg-red-500 border-dashed border-t"></div>
                    <span className="text-gray-300 text-xs">High Impact</span>
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-4 h-1 bg-orange-500 border-dashed border-t"></div>
                    <span className="text-gray-300 text-xs">Medium Impact</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-1 bg-gray-500 border-dashed border-t"></div>
                    <span className="text-gray-300 text-xs">Low Impact</span>
                  </div>
                </div>
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Instructions */}
        <div className="bg-gray-900 border-t border-gray-800 p-3 text-center text-gray-400 text-sm">
          💡 Click on chapters to view details • Drag to pan • Scroll to zoom • Use controls to fit view
        </div>
      </div>
    </div>
  );
};

export default StoryTreeVisualization; 