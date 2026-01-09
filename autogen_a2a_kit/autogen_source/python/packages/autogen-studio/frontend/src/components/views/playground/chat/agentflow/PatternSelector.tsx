/**
 * PatternSelector Component
 *
 * Card-based visual pattern selector for choosing collaboration patterns.
 * Displays patterns as cards with icons, descriptions, and visual previews.
 */

import React, { useState } from "react";
import {
  ArrowRight,
  RefreshCw,
  GitBranch,
  Share2,
  Layers,
  MessageCircle,
  Users,
  GitMerge,
} from "lucide-react";
import {
  PATTERN_LIBRARY,
  PatternDefinition,
  PatternCategory,
} from "./patterns/pattern-schema";

interface PatternSelectorProps {
  selectedPattern: string;
  onPatternSelect: (patternId: string) => void;
  className?: string;
}

// Icon mapping
const patternIcons: Record<string, React.ReactNode> = {
  "arrow-right-circle": <ArrowRight className="w-6 h-6" />,
  "refresh-cw": <RefreshCw className="w-6 h-6" />,
  "git-branch": <GitBranch className="w-6 h-6" />,
  "share-2": <Share2 className="w-6 h-6" />,
  "layers": <Layers className="w-6 h-6" />,
  "message-circle": <MessageCircle className="w-6 h-6" />,
  "users": <Users className="w-6 h-6" />,
  "git-merge": <GitMerge className="w-6 h-6" />,
};

// Mini preview SVG for each pattern
const PatternPreview: React.FC<{ pattern: PatternDefinition }> = ({ pattern }) => {
  const { layout, primaryColor, secondaryColor } = pattern.visual;

  const previewStyles: Record<string, React.ReactNode> = {
    chain: (
      <svg viewBox="0 0 80 30" className="w-full h-8">
        <circle cx="10" cy="15" r="5" fill={primaryColor} />
        <line x1="15" y1="15" x2="30" y2="15" stroke={primaryColor} strokeWidth="2" />
        <circle cx="35" cy="15" r="5" fill={primaryColor} />
        <line x1="40" y1="15" x2="55" y2="15" stroke={primaryColor} strokeWidth="2" />
        <circle cx="60" cy="15" r="5" fill={primaryColor} />
        <line x1="65" y1="15" x2="80" y2="15" stroke={primaryColor} strokeWidth="2" markerEnd="url(#arrow)" />
      </svg>
    ),
    "hub-spoke": (
      <svg viewBox="0 0 80 40" className="w-full h-10">
        <circle cx="40" cy="20" r="8" fill={primaryColor} />
        <circle cx="15" cy="10" r="4" fill={secondaryColor} />
        <circle cx="15" cy="30" r="4" fill={secondaryColor} />
        <circle cx="65" cy="10" r="4" fill={secondaryColor} />
        <circle cx="65" cy="30" r="4" fill={secondaryColor} />
        <line x1="32" y1="18" x2="19" y2="12" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="32" y1="22" x2="19" y2="28" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="48" y1="18" x2="61" y2="12" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="48" y1="22" x2="61" y2="28" stroke={primaryColor} strokeWidth="1.5" />
      </svg>
    ),
    mesh: (
      <svg viewBox="0 0 80 40" className="w-full h-10">
        <circle cx="40" cy="8" r="4" fill={primaryColor} />
        <circle cx="20" cy="32" r="4" fill={secondaryColor} />
        <circle cx="60" cy="32" r="4" fill={secondaryColor} />
        <line x1="40" y1="12" x2="22" y2="28" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="40" y1="12" x2="58" y2="28" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="24" y1="32" x2="56" y2="32" stroke={secondaryColor} strokeWidth="1.5" strokeDasharray="3,2" />
      </svg>
    ),
    "fork-join": (
      <svg viewBox="0 0 80 40" className="w-full h-10">
        <rect x="5" y="16" width="10" height="8" rx="2" fill={primaryColor} />
        <circle cx="35" cy="8" r="4" fill={secondaryColor} />
        <circle cx="35" cy="20" r="4" fill={secondaryColor} />
        <circle cx="35" cy="32" r="4" fill={secondaryColor} />
        <rect x="55" y="16" width="10" height="8" rx="2" fill={primaryColor} />
        <line x1="15" y1="20" x2="31" y2="8" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="15" y1="20" x2="31" y2="20" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="15" y1="20" x2="31" y2="32" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="39" y1="8" x2="55" y2="20" stroke={secondaryColor} strokeWidth="1.5" />
        <line x1="39" y1="20" x2="55" y2="20" stroke={secondaryColor} strokeWidth="1.5" />
        <line x1="39" y1="32" x2="55" y2="20" stroke={secondaryColor} strokeWidth="1.5" />
      </svg>
    ),
    tree: (
      <svg viewBox="0 0 80 40" className="w-full h-10">
        <circle cx="40" cy="8" r="5" fill={primaryColor} />
        <circle cx="20" cy="32" r="4" fill={secondaryColor} />
        <circle cx="40" cy="32" r="4" fill={secondaryColor} />
        <circle cx="60" cy="32" r="4" fill={secondaryColor} />
        <line x1="38" y1="13" x2="22" y2="28" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="40" y1="13" x2="40" y2="28" stroke={primaryColor} strokeWidth="1.5" />
        <line x1="42" y1="13" x2="58" y2="28" stroke={primaryColor} strokeWidth="1.5" />
      </svg>
    ),
    ring: (
      <svg viewBox="0 0 80 40" className="w-full h-10">
        <circle cx="40" cy="8" r="4" fill={primaryColor} />
        <circle cx="20" cy="32" r="4" fill={primaryColor} />
        <circle cx="60" cy="32" r="4" fill={primaryColor} />
        <line x1="38" y1="12" x2="22" y2="28" stroke={secondaryColor} strokeWidth="1.5" strokeDasharray="3,2" />
        <line x1="42" y1="12" x2="58" y2="28" stroke={secondaryColor} strokeWidth="1.5" strokeDasharray="3,2" />
        <line x1="24" y1="32" x2="56" y2="32" stroke={secondaryColor} strokeWidth="1.5" strokeDasharray="3,2" />
      </svg>
    ),
  };

  return previewStyles[layout] || previewStyles.chain;
};

// Category labels
const categoryLabels: Record<PatternCategory, { label: string; description: string }> = {
  sequential: { label: "Sequential", description: "Fixed order execution" },
  dynamic: { label: "Dynamic", description: "Runtime agent selection" },
  parallel: { label: "Parallel", description: "Concurrent execution" },
  hierarchical: { label: "Hierarchical", description: "Multi-level coordination" },
};

// Group patterns by category
const groupedPatterns = PATTERN_LIBRARY.reduce((acc, pattern) => {
  if (!acc[pattern.category]) {
    acc[pattern.category] = [];
  }
  acc[pattern.category].push(pattern);
  return acc;
}, {} as Record<PatternCategory, PatternDefinition[]>);

export const PatternSelector: React.FC<PatternSelectorProps> = ({
  selectedPattern,
  onPatternSelect,
  className = "",
}) => {
  const [expandedCategory, setExpandedCategory] = useState<PatternCategory | null>(null);

  return (
    <div className={`pattern-selector ${className}`}>
      {Object.entries(groupedPatterns).map(([category, patterns]) => (
        <div key={category} className="mb-4">
          {/* Category Header */}
          <button
            onClick={() =>
              setExpandedCategory(
                expandedCategory === category ? null : (category as PatternCategory)
              )
            }
            className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-secondary bg-secondary rounded-t hover:bg-tertiary transition-colors"
          >
            <span>{categoryLabels[category as PatternCategory].label}</span>
            <span className="text-xs opacity-60">
              {categoryLabels[category as PatternCategory].description}
            </span>
          </button>

          {/* Pattern Cards */}
          <div
            className={`grid grid-cols-1 gap-2 p-2 bg-primary border border-secondary rounded-b transition-all ${
              expandedCategory === category ? "block" : "hidden"
            }`}
          >
            {patterns.map((pattern) => (
              <button
                key={pattern.id}
                onClick={() => onPatternSelect(pattern.id)}
                className={`flex flex-col p-3 rounded-lg border-2 transition-all hover:shadow-md ${
                  selectedPattern === pattern.id
                    ? "border-accent bg-accent/10"
                    : "border-secondary hover:border-accent/50"
                }`}
              >
                {/* Header */}
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="p-1.5 rounded"
                    style={{ backgroundColor: pattern.visual.primaryColor + "20" }}
                  >
                    <span style={{ color: pattern.visual.primaryColor }}>
                      {patternIcons[pattern.visual.icon]}
                    </span>
                  </div>
                  <div className="flex-1 text-left">
                    <div className="font-medium text-primary">{pattern.name}</div>
                    <div className="text-xs text-secondary">{pattern.description}</div>
                  </div>
                </div>

                {/* Visual Preview */}
                <div className="mt-2 p-2 bg-secondary/30 rounded">
                  <PatternPreview pattern={pattern} />
                </div>

                {/* Use Cases */}
                <div className="mt-2 flex flex-wrap gap-1">
                  {pattern.useCases.slice(0, 2).map((useCase, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-2 py-0.5 bg-secondary rounded-full text-secondary"
                    >
                      {useCase}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Compact Pattern Selector for inline use
 */
export const PatternSelectorCompact: React.FC<PatternSelectorProps> = ({
  selectedPattern,
  onPatternSelect,
  className = "",
}) => {
  const selected = PATTERN_LIBRARY.find((p) => p.id === selectedPattern);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex gap-1">
        {PATTERN_LIBRARY.filter(
          (p) => ["sequential", "selector", "swarm"].includes(p.id)
        ).map((pattern) => (
          <button
            key={pattern.id}
            onClick={() => onPatternSelect(pattern.id)}
            className={`flex items-center gap-1 px-2 py-1 text-xs rounded transition-all ${
              selectedPattern === pattern.id
                ? "bg-accent text-white"
                : "bg-secondary text-secondary hover:bg-tertiary"
            }`}
            title={pattern.description}
          >
            <span style={{ color: selectedPattern === pattern.id ? "white" : pattern.visual.primaryColor }}>
              {patternIcons[pattern.visual.icon]}
            </span>
            <span className="hidden sm:inline">{pattern.name.split(" ")[0]}</span>
          </button>
        ))}
      </div>
      {selected && (
        <span className="text-xs text-secondary hidden md:inline">
          {selected.description}
        </span>
      )}
    </div>
  );
};

export default PatternSelector;
