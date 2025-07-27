import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ReactFlow, { 
  MiniMap, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState,
  ConnectionLineType,
  Position,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { TreePine, Loader2, Users, BookOpen, Clock, Zap, CheckCircle, Circle, ArrowRight } from 'lucide-react';
import { createApiUrl } from '../config';
import { useAuth } from '../AuthContext';

// Custom Chapter Node Component
const ChapterNode = ({ data, isConnectable }) => {
  const { chapter, onNavigate, isSelected, isCurrent } = data;
  
  return (
    <div className={`px-4 py-3 shadow-lg rounded-xl border-2 bg-gray-800 min-w-[200px] transition-all duration-300 hover:scale-105 ${
      isCurrent ? 'border-blue-500 ring-2 ring-blue-400/50' : 
      isSelected ? 'border-green-500' : 'border-gray-600'
    }`}>
      <div className="flex items-center space-x-3">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white ${
          isCurrent ? 'bg-blue-600' : isSelected ? 'bg-green-600' : 'bg-gray-600'
        }`}>
          {chapter.chapter_number}
        </div>
        <div className="flex-1">
          <div className="text-white font-medium text-sm">{chapter.title}</div>
          <div className="text-gray-400 text-xs">{chapter.word_count} words</div>
          {isCurrent && (
            <div className="text-blue-400 text-xs font-medium">CURRENT</div>
          )}
        </div>
      </div>
      
      <button
        onClick={() => onNavigate(chapter.chapter_number)}
        className="mt-2 w-full px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
      >
        Jump to Chapter
      </button>
    </div>
  );
};

// Custom Choice Node Component  
const ChoiceNode = ({ data, isConnectable }) => {
  const { choice, isSelected } = data;
  
  return (
    <div className={`px-3 py-2 shadow-md rounded-lg border transition-all duration-300 hover:scale-105 max-w-[180px] ${
      isSelected 
        ? 'bg-green-900/30 border-green-500/50 shadow-green-500/20' 
        : 'bg-gray-800/50 border-gray-600/30'
    }`}>
      <div className="flex items-center space-x-2">
        {isSelected ? (
          <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
        ) : (
          <Circle className="w-4 h-4 text-gray-500 flex-shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <div className={`text-xs font-medium ${
            isSelected ? 'text-green-300' : 'text-gray-300'
          }`}>
            {choice.title}
          </div>
          {choice.story_impact && (
            <div className={`text-xs mt-1 px-1 py-0.5 rounded ${
              choice.story_impact === 'high' ? 'bg-red-900/30 text-red-400' :
              choice.story_impact === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
              'bg-blue-900/30 text-blue-400'
            }`}>
              {choice.story_impact}
            </div>
          )}
        </div>
        {isSelected && <ArrowRight className="w-3 h-3 text-green-400 flex-shrink-0" />}
      </div>
    </div>
  );
};

// Define custom node types
const nodeTypes = {
  chapter: ChapterNode,
  choice: ChoiceNode,
};

const StoryTree = ({ storyId, chapters, onChapterSelect }) => {
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const { session } = useAuth();
  
  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // OPTIMIZATION: Memoized navigation function (define this FIRST)
  const handleChapterNavigation = useCallback((chapterNumber) => {
    onChapterSelect(`chapter-${chapterNumber}`);
  }, [onChapterSelect]);

  // Transform story data to React Flow format
  const transformStoryDataToFlow = useCallback((storyData) => {
    const flowNodes = [];
    const flowEdges = [];
    
    let yPosition = 0;
    const VERTICAL_SPACING = 200;
    const CHOICE_SPACING = 120;
    
    storyData.forEach((chapterNode, chapterIndex) => {
      const { chapter, choices, choice_stats, is_current_chapter } = chapterNode;
      
      // Create chapter node
      const chapterNodeId = `chapter-${chapter.chapter_number}`;
      flowNodes.push({
        id: chapterNodeId,
        type: 'chapter',
        position: { x: 0, y: yPosition },
        data: {
          chapter,
          onNavigate: handleChapterNavigation,
          isSelected: choice_stats?.selected > 0,
          isCurrent: is_current_chapter,
        },
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });
      
      yPosition += VERTICAL_SPACING;
      
      // Create choice nodes if they exist
      if (choices && choices.length > 0) {
        const choiceStartX = -(choices.length - 1) * CHOICE_SPACING / 2;
        
        choices.forEach((choice, choiceIndex) => {
          const choiceNodeId = `choice-${chapter.chapter_number}-${choice.id}`;
          const choiceX = choiceStartX + (choiceIndex * CHOICE_SPACING);
          
          // Create choice node
          flowNodes.push({
            id: choiceNodeId,
            type: 'choice',
            position: { x: choiceX, y: yPosition },
            data: {
              choice,
              isSelected: choice.selected,
            },
            sourcePosition: Position.Bottom,
            targetPosition: Position.Top,
          });
          
          // Edge from chapter to choice
          flowEdges.push({
            id: `edge-${chapterNodeId}-${choiceNodeId}`,
            source: chapterNodeId,
            target: choiceNodeId,
            type: 'smoothstep',
            animated: choice.selected,
            style: {
              stroke: choice.selected ? '#10b981' : '#6b7280',
              strokeWidth: choice.selected ? 3 : 1,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: choice.selected ? '#10b981' : '#6b7280',
            },
          });
          
          // Edge from selected choice to next chapter
          if (choice.selected && chapterIndex < storyData.length - 1) {
            const nextChapterNodeId = `chapter-${storyData[chapterIndex + 1].chapter.chapter_number}`;
            flowEdges.push({
              id: `edge-${choiceNodeId}-${nextChapterNodeId}`,
              source: choiceNodeId,
              target: nextChapterNodeId,
              type: 'smoothstep',
              animated: true,
              style: {
                stroke: '#10b981',
                strokeWidth: 3,
              },
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: '#10b981',
              },
            });
          }
        });
        
        yPosition += VERTICAL_SPACING;
      }
    });
    
    return { nodes: flowNodes, edges: flowEdges };
  }, [handleChapterNavigation]);

  // OPTIMIZATION: Memoized fetch function
  const fetchTreeData = useCallback(async () => {
    if (!storyId || !session?.access_token) return;
    
    setLoading(true);
    setError('');
    const startTime = performance.now();
    
    try {
      const response = await fetch(createApiUrl(`/story/${storyId}/tree`), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch tree data: ${response.status}`);
      }
      
      const data = await response.json();
      const fetchTime = performance.now() - startTime;
      
      console.log('🌳 Optimized tree data fetched in', fetchTime.toFixed(2), 'ms:', data);
      
      if (data.success) {
        setTreeData(data.tree);
        setPerformanceMetrics({
          frontend_fetch_time: Math.round(fetchTime),
          backend_query_time: data.performance?.query_time || 0,
          total_chapters: data.total_chapters,
          total_choices: data.total_choices,
          optimization: data.performance?.optimization
        });
        
        // Transform data and update React Flow
        const { nodes: flowNodes, edges: flowEdges } = transformStoryDataToFlow(data.tree);
        setNodes(flowNodes);
        setEdges(flowEdges);
      } else {
        setError(data.message || 'Failed to load story tree');
      }
    } catch (err) {
      console.error('Error fetching tree data:', err);
      setError('Failed to load story tree data');
    } finally {
      setLoading(false);
    }
  }, [storyId, session, transformStoryDataToFlow]);

  // Fetch tree data when dependencies change
  useEffect(() => {
    fetchTreeData();
  }, [fetchTreeData]);

  // React Flow configuration
  const defaultEdgeOptions = {
    animated: false,
    type: 'smoothstep',
    style: { strokeWidth: 2 },
  };

  const proOptions = {
    hideAttribution: true,
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-lg h-[600px] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
          <span className="text-gray-300">Loading interactive story tree...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-lg h-[600px] flex items-center justify-center">
        <div className="text-center p-6">
          <TreePine className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">Story Tree Error</h3>
          <p className="text-red-300 text-sm mb-4">❌ {error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  }

  // Show empty state if no tree data
  if (!treeData || treeData.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-lg h-[600px] flex items-center justify-center">
        <div className="text-center p-6">
          <TreePine className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">No Story Data</h3>
          <p className="text-gray-400 text-sm">
            Start writing chapters with choices to see the interactive tree visualization
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden h-[600px]">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TreePine className="w-6 h-6 text-green-400" />
            <h2 className="text-xl font-bold text-white">Interactive Story Tree</h2>
          </div>
          
          {/* Story Stats */}
          <div className="flex items-center space-x-4 text-xs text-gray-400">
            <span className="flex items-center space-x-1">
              <BookOpen className="w-3 h-3" />
              <span>{treeData ? treeData.length : 0} chapters</span>
            </span>
            <span className="flex items-center space-x-1">
              <Users className="w-3 h-3" />
              <span>{treeData ? treeData.reduce((sum, node) => sum + node.choices.length, 0) : 0} choices</span>
            </span>
            {performanceMetrics && (
              <span className="flex items-center space-x-1">
                <Zap className="w-3 h-3" />
                <span>{performanceMetrics.backend_query_time}s</span>
              </span>
            )}
          </div>
        </div>
        
        {/* Description */}
        <p className="text-gray-400 text-sm mt-2">
          🌳 Interactive tree view • Drag to pan • Scroll to zoom • Click chapters to navigate
        </p>
      </div>

      {/* React Flow Tree */}
      <div className="h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          connectionLineType={ConnectionLineType.SmoothStep}
          fitView
          fitViewOptions={{
            padding: 50,
            minZoom: 0.5,
            maxZoom: 1.5,
          }}
          proOptions={proOptions}
          className="bg-gray-900"
        >
          <Controls 
            className="bg-gray-800 border border-gray-600"
            showInteractive={false}
          />
          <MiniMap 
            className="bg-gray-800 border border-gray-600"
            nodeColor="#374151"
            maskColor="rgba(0, 0, 0, 0.2)"
          />
          <Background 
            variant="dots" 
            gap={20} 
            size={1} 
            color="#374151"
          />
        </ReactFlow>
      </div>
      
      {/* Footer with performance metrics */}
      {performanceMetrics && (
        <div className="p-3 bg-gray-700/50 border-t border-gray-600">
          <div className="text-xs text-gray-400 text-center">
            🚀 Interactive Tree • {performanceMetrics.optimization?.replace('_', ' ')} • 
            Loaded {performanceMetrics.total_chapters} chapters + {performanceMetrics.total_choices} choices 
            in {(performanceMetrics.backend_query_time + (performanceMetrics.frontend_fetch_time/1000)).toFixed(2)}s
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryTree; 