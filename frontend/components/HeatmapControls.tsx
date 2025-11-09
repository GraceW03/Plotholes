"use client";

import { useState } from "react";
import { Layers, MapPin, Grid3X3, Eye, EyeOff } from "lucide-react";

export type HeatmapMode = 'off' | 'individual' | 'neighborhoods';

interface HeatmapControlsProps {
  mode: HeatmapMode;
  onModeChange: (mode: HeatmapMode) => void;
  isLoading?: boolean;
}

export default function HeatmapControls({ mode, onModeChange, isLoading = false }: HeatmapControlsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const modes = [
    {
      key: 'off' as HeatmapMode,
      label: 'Off',
      icon: EyeOff,
      description: 'Hide heatmap',
      color: 'text-gray-500'
    },
    {
      key: 'individual' as HeatmapMode,
      label: 'Issues',
      icon: MapPin,
      description: 'Individual issue severity',
      color: 'text-red-500'
    },
    {
      key: 'neighborhoods' as HeatmapMode,
      label: 'Neighborhoods',
      icon: Grid3X3,
      description: 'Neighborhood risk levels',
      color: 'text-orange-500'
    }
  ];

  return (
    <div className="absolute top-4 right-4 z-[1000] bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
        disabled={isLoading}
      >
        <Layers size={18} />
        <span>Heatmap</span>
        {isLoading && (
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600"></div>
        )}
      </button>

      {/* Expanded Controls */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-2">
          <div className="space-y-1">
            {modes.map((modeOption) => {
              const Icon = modeOption.icon;
              const isActive = mode === modeOption.key;

              return (
                <button
                  key={modeOption.key}
                  onClick={() => onModeChange(modeOption.key)}
                  disabled={isLoading}
                  className={`
                    w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors text-left
                    ${isActive
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'text-gray-600 hover:bg-gray-50'
                    }
                    ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  <Icon
                    size={16}
                    className={isActive ? 'text-blue-600' : modeOption.color}
                  />
                  <div className="flex-1">
                    <div className="font-medium">{modeOption.label}</div>
                    <div className="text-xs text-gray-500">{modeOption.description}</div>
                  </div>
                  {isActive && (
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Info */}
          <div className="mt-3 pt-2 border-t border-gray-100">
            <div className="text-xs text-gray-500 px-1">
              {mode === 'individual' && 'Shows severity of individual street issues'}
              {mode === 'neighborhoods' && 'Shows aggregated risk levels by neighborhood'}
              {mode === 'off' && 'Heatmap is currently disabled'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}