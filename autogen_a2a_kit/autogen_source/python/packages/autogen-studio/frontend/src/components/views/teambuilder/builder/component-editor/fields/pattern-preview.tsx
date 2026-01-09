import React, { useMemo, useEffect, useState } from "react";
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  MarkerType,
  Position,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Bot, Users, ArrowRight, Loader2 } from "lucide-react";
import {
  Component,
  TeamConfig,
  AgentConfig,
} from "../../../../../types/datamodel";

// Check if we're in browser environment
const isBrowser = typeof window !== "undefined";

interface PatternPreviewProps {
  component: Component<TeamConfig>;
}

type PatternType = "sequential" | "selector" | "handoff" | "debate" | "reflection" | "unknown";

// Determine pattern type from team configuration
const getPatternType = (component: Component<TeamConfig>): PatternType => {
  const provider = component.provider || "";
  const participants = component.config?.participants || [];

  if (provider.includes("Swarm")) {
    return "handoff";
  }

  if (provider.includes("SelectorGroupChat")) {
    // Check for debate pattern (advocate, critic, judge)
    const names = participants.map((p: Component<AgentConfig>) =>
      p.config?.name?.toLowerCase() || ""
    );
    if (names.some((n: string) => n.includes("advocate") || n.includes("judge") || n.includes("critic"))) {
      return "debate";
    }
    return "selector";
  }

  if (provider.includes("RoundRobinGroupChat")) {
    // Check for reflection pattern (generator + critic with approval)
    const names = participants.map((p: Component<AgentConfig>) =>
      p.config?.name?.toLowerCase() || ""
    );
    if (participants.length === 2 &&
        (names.some((n: string) => n.includes("generator") || n.includes("writer")) &&
         names.some((n: string) => n.includes("critic") || n.includes("reviewer")))) {
      return "reflection";
    }
    return "sequential";
  }

  return "unknown";
};

// Generate nodes and edges based on pattern type
const generatePatternElements = (
  component: Component<TeamConfig>,
  patternType: PatternType
): { nodes: Node[]; edges: Edge[] } => {
  const participants = component.config?.participants || [];
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const nodeStyle = {
    padding: "10px 15px",
    borderRadius: "8px",
    border: "1px solid #374151",
    background: "#1f2937",
    color: "#e5e7eb",
    fontSize: "12px",
    fontWeight: 500,
  };

  const activeNodeStyle = {
    ...nodeStyle,
    border: "2px solid #3b82f6",
    background: "#1e3a5f",
  };

  switch (patternType) {
    case "sequential": {
      // Linear flow: A → B → C
      const spacing = 180;
      participants.forEach((p: Component<AgentConfig>, index: number) => {
        nodes.push({
          id: `agent-${index}`,
          position: { x: index * spacing, y: 50 },
          data: {
            label: (
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4" />
                <span>{p.config?.name || `Agent ${index + 1}`}</span>
              </div>
            )
          },
          style: nodeStyle,
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        });

        if (index > 0) {
          edges.push({
            id: `e-${index-1}-${index}`,
            source: `agent-${index - 1}`,
            target: `agent-${index}`,
            type: "smoothstep",
            animated: true,
            markerEnd: { type: MarkerType.ArrowClosed, color: "#6b7280" },
            style: { stroke: "#6b7280", strokeWidth: 2 },
          });
        }
      });
      break;
    }

    case "selector": {
      // Hub and spoke: Central selector with specialists around it
      const centerX = 200;
      const centerY = 120;
      const radius = 120;

      // Add central selector/router node
      nodes.push({
        id: "selector",
        position: { x: centerX - 50, y: centerY - 20 },
        data: {
          label: (
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-400" />
              <span>Selector</span>
            </div>
          )
        },
        style: activeNodeStyle,
      });

      // Add specialist agents around the selector
      participants.forEach((p: Component<AgentConfig>, index: number) => {
        const angle = (2 * Math.PI * index) / participants.length - Math.PI / 2;
        const x = centerX + radius * Math.cos(angle) - 40;
        const y = centerY + radius * Math.sin(angle);

        nodes.push({
          id: `agent-${index}`,
          position: { x, y },
          data: {
            label: (
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4" />
                <span>{p.config?.name || `Agent ${index + 1}`}</span>
              </div>
            )
          },
          style: nodeStyle,
        });

        edges.push({
          id: `e-selector-${index}`,
          source: "selector",
          target: `agent-${index}`,
          type: "smoothstep",
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed, color: "#6b7280" },
          style: { stroke: "#6b7280", strokeWidth: 2 },
        });
      });
      break;
    }

    case "handoff": {
      // Dynamic handoff: Triage center with bidirectional connections
      if (participants.length === 0) break;

      const centerX = 200;
      const centerY = 100;

      // Find triage agent (usually first or named "triage")
      const triageIndex = participants.findIndex((p: Component<AgentConfig>) =>
        p.config?.name?.toLowerCase().includes("triage")
      );
      const actualTriageIndex = triageIndex >= 0 ? triageIndex : 0;
      const triageAgent = participants[actualTriageIndex];
      const otherAgents = participants.filter((_: Component<AgentConfig>, i: number) =>
        i !== actualTriageIndex
      );

      // Add triage node at center
      nodes.push({
        id: "triage",
        position: { x: centerX - 50, y: centerY - 20 },
        data: {
          label: (
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-yellow-400" />
              <span>{triageAgent?.config?.name || "Triage"}</span>
            </div>
          )
        },
        style: activeNodeStyle,
      });

      // Add other agents
      const radius = 110;
      otherAgents.forEach((p: Component<AgentConfig>, index: number) => {
        const angle = (2 * Math.PI * index) / otherAgents.length - Math.PI / 2;
        const x = centerX + radius * Math.cos(angle) - 40;
        const y = centerY + radius * Math.sin(angle);

        nodes.push({
          id: `agent-${index}`,
          position: { x, y },
          data: {
            label: (
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4" />
                <span>{p.config?.name || `Agent ${index + 1}`}</span>
              </div>
            )
          },
          style: nodeStyle,
        });

        // Bidirectional edges for handoff
        edges.push({
          id: `e-triage-${index}`,
          source: "triage",
          target: `agent-${index}`,
          type: "smoothstep",
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed, color: "#22c55e" },
          style: { stroke: "#22c55e", strokeWidth: 2 },
        });

        edges.push({
          id: `e-${index}-triage`,
          source: `agent-${index}`,
          target: "triage",
          type: "smoothstep",
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed, color: "#f59e0b" },
          style: { stroke: "#f59e0b", strokeWidth: 2, strokeDasharray: "5,5" },
        });
      });
      break;
    }

    case "debate": {
      // Debate: Advocate ←→ Critic → Judge
      nodes.push({
        id: "advocate",
        position: { x: 50, y: 50 },
        data: {
          label: (
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-green-400" />
              <span>Advocate</span>
            </div>
          )
        },
        style: { ...nodeStyle, border: "2px solid #22c55e" },
      });

      nodes.push({
        id: "critic",
        position: { x: 250, y: 50 },
        data: {
          label: (
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-red-400" />
              <span>Critic</span>
            </div>
          )
        },
        style: { ...nodeStyle, border: "2px solid #ef4444" },
      });

      nodes.push({
        id: "judge",
        position: { x: 150, y: 150 },
        data: {
          label: (
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-400" />
              <span>Judge</span>
            </div>
          )
        },
        style: activeNodeStyle,
      });

      // Bidirectional debate arrows
      edges.push({
        id: "e-adv-crit",
        source: "advocate",
        target: "critic",
        type: "smoothstep",
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: "#22c55e" },
        style: { stroke: "#22c55e", strokeWidth: 2 },
        label: "argue",
        labelStyle: { fill: "#9ca3af", fontSize: 10 },
      });

      edges.push({
        id: "e-crit-adv",
        source: "critic",
        target: "advocate",
        type: "smoothstep",
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: "#ef4444" },
        style: { stroke: "#ef4444", strokeWidth: 2 },
        label: "counter",
        labelStyle: { fill: "#9ca3af", fontSize: 10 },
      });

      edges.push({
        id: "e-adv-judge",
        source: "advocate",
        target: "judge",
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, color: "#6b7280" },
        style: { stroke: "#6b7280", strokeWidth: 1.5, strokeDasharray: "3,3" },
      });

      edges.push({
        id: "e-crit-judge",
        source: "critic",
        target: "judge",
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, color: "#6b7280" },
        style: { stroke: "#6b7280", strokeWidth: 1.5, strokeDasharray: "3,3" },
      });
      break;
    }

    case "reflection": {
      // Reflection: Generator ←→ Critic (loop until approved)
      nodes.push({
        id: "generator",
        position: { x: 50, y: 60 },
        data: {
          label: (
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-blue-400" />
              <span>Generator</span>
            </div>
          )
        },
        style: { ...nodeStyle, border: "2px solid #3b82f6" },
      });

      nodes.push({
        id: "critic",
        position: { x: 250, y: 60 },
        data: {
          label: (
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-yellow-400" />
              <span>Critic</span>
            </div>
          )
        },
        style: { ...nodeStyle, border: "2px solid #f59e0b" },
      });

      // Output node
      nodes.push({
        id: "output",
        position: { x: 150, y: 150 },
        data: {
          label: (
            <div className="flex items-center gap-2 text-green-400">
              <ArrowRight className="w-4 h-4" />
              <span>APPROVED</span>
            </div>
          )
        },
        style: { ...nodeStyle, border: "2px solid #22c55e", background: "#14532d" },
      });

      // Generate → Critic
      edges.push({
        id: "e-gen-crit",
        source: "generator",
        target: "critic",
        type: "smoothstep",
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: "#3b82f6" },
        style: { stroke: "#3b82f6", strokeWidth: 2 },
        label: "output",
        labelStyle: { fill: "#9ca3af", fontSize: 10 },
      });

      // Critic → Generator (feedback loop)
      edges.push({
        id: "e-crit-gen",
        source: "critic",
        target: "generator",
        type: "smoothstep",
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: "#f59e0b" },
        style: { stroke: "#f59e0b", strokeWidth: 2 },
        label: "feedback",
        labelStyle: { fill: "#9ca3af", fontSize: 10 },
      });

      // Critic → Output (when approved)
      edges.push({
        id: "e-crit-out",
        source: "critic",
        target: "output",
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, color: "#22c55e" },
        style: { stroke: "#22c55e", strokeWidth: 2, strokeDasharray: "5,5" },
      });
      break;
    }

    default: {
      // Unknown: Simple list of agents
      participants.forEach((p: Component<AgentConfig>, index: number) => {
        nodes.push({
          id: `agent-${index}`,
          position: { x: 50, y: index * 60 + 20 },
          data: {
            label: (
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4" />
                <span>{p.config?.name || `Agent ${index + 1}`}</span>
              </div>
            )
          },
          style: nodeStyle,
        });
      });
    }
  }

  return { nodes, edges };
};

// Pattern type labels and colors
const patternLabels: Record<PatternType, { label: string; color: string; description: string }> = {
  sequential: {
    label: "Sequential",
    color: "bg-blue-500",
    description: "Agents take turns in a fixed order"
  },
  selector: {
    label: "Selector",
    color: "bg-purple-500",
    description: "Central router selects the best agent"
  },
  handoff: {
    label: "Handoff",
    color: "bg-yellow-500",
    description: "Agents dynamically transfer control"
  },
  debate: {
    label: "Debate",
    color: "bg-red-500",
    description: "Agents argue different perspectives"
  },
  reflection: {
    label: "Reflection",
    color: "bg-green-500",
    description: "Iterative improvement through feedback"
  },
  unknown: {
    label: "Custom",
    color: "bg-gray-500",
    description: "Custom team configuration"
  },
};

const PatternPreviewInner: React.FC<PatternPreviewProps> = ({ component }) => {
  const { fitView } = useReactFlow();
  const patternType = useMemo(() => getPatternType(component), [component]);
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => generatePatternElements(component, patternType),
    [component, patternType]
  );

  const [nodes, setNodes] = useNodesState(initialNodes);
  const [edges, setEdges] = useEdgesState(initialEdges);

  // Update nodes/edges when component changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    // Refit view after nodes change
    setTimeout(() => fitView({ padding: 0.3 }), 50);
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView]);

  const patternInfo = patternLabels[patternType];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs text-white ${patternInfo.color}`}>
            {patternInfo.label}
          </span>
          <span className="text-sm text-secondary">{patternInfo.description}</span>
        </div>
        <span className="text-xs text-secondary">
          {component.config?.participants?.length || 0} agents
        </span>
      </div>

      <div
        className="rounded border border-secondary overflow-hidden"
        style={{ width: "100%", height: "220px", background: "#111827" }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          minZoom={0.5}
          maxZoom={1.5}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag={false}
          zoomOnScroll={false}
          preventScrolling={true}
        >
          <Background color="#374151" gap={20} size={1} />
        </ReactFlow>
      </div>
    </div>
  );
};

export const PatternPreview: React.FC<PatternPreviewProps> = ({ component }) => {
  // Only render on client side to avoid SSR hydration issues
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Show loading placeholder during SSR and initial client render
  if (!isBrowser || !mounted) {
    const patternType = getPatternType(component);
    const patternInfo = patternLabels[patternType];

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded text-xs text-white ${patternInfo.color}`}>
              {patternInfo.label}
            </span>
            <span className="text-sm text-secondary">{patternInfo.description}</span>
          </div>
          <span className="text-xs text-secondary">
            {component.config?.participants?.length || 0} agents
          </span>
        </div>
        <div
          className="rounded border border-secondary overflow-hidden flex items-center justify-center"
          style={{ width: "100%", height: "220px", background: "#111827" }}
        >
          <div className="flex items-center gap-2 text-secondary">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-sm">Loading diagram...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <PatternPreviewInner component={component} />
    </ReactFlowProvider>
  );
};

export default PatternPreview;
