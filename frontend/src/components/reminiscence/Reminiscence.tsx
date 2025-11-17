import React from "react";
import { QuoteExplorer } from "./QuoteExplorer";
import { CharacterMomentsTimeline } from "./CharacterMomentsTimeline";
import { SeasonComparison } from "./SeasonComparison";

type ReminiscenceTab = "quotes" | "moments" | "seasons";

export const Reminiscence: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState<ReminiscenceTab>("quotes");

  const tabs = [
    { id: "quotes" as ReminiscenceTab, name: "Quote Explorer", icon: "💬" },
    { id: "moments" as ReminiscenceTab, name: "Character Moments", icon: "🎭" },
    { id: "seasons" as ReminiscenceTab, name: "Season Comparison", icon: "📊" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Reminiscence</h1>
        <p className="text-sm text-gray-600">
          Explore memorable quotes, character moments, and compare seasons to relive your favorite show.
        </p>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-gray-200 pb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.name}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {activeTab === "quotes" && <QuoteExplorer />}
        {activeTab === "moments" && <CharacterMomentsTimeline />}
        {activeTab === "seasons" && <SeasonComparison />}
      </div>
    </div>
  );
};

