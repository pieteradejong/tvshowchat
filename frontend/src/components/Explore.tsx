import { FC, useMemo } from 'react';
import { PromptExamples, PromptCategory, DEFAULT_PROMPT_CATEGORIES } from './PromptExamples';

interface ExploreProps {
  onSelectPrompt?: (prompt: string) => void;
}

const HOW_IT_WORKS: PromptCategory[] = [
  {
    title: 'Mood-based watchlists',
    icon: '🎧',
    description:
      'Find Buffy episodes that match a vibe—comfort, spooky, or musical nights—and save them for later.',
    prompts: [
      'What are three comfort episodes with heartwarming Scooby dynamics?',
      'Give me a musical-centric Buffy mini marathon.',
      'Recommend chilling Buffy episodes for a Halloween watch party.',
    ],
  },
  {
    title: 'Character journeys',
    icon: '🧙‍♀️',
    description:
      'Track how a character grows across seasons, with summaries to revisit key turning points.',
    prompts: [
      'Episodes that chart Willow’s relationship with magic from novice to powerful witch.',
      'Follow Buffy’s leadership choices after she comes back in Season 6.',
      'Spike’s redemption path episodes to watch in order.',
    ],
  },
  {
    title: 'Theme deep dives',
    icon: '🧩',
    description:
      'Surface episodes tied together by core themes like grief, power, or friendship.',
    prompts: [
      'Episodes exploring the cost of power and responsibility.',
      'Find episodes where friendship literally saves the day.',
      'How does the show tackle grief across different seasons?',
    ],
  },
];

export const Explore: FC<ExploreProps> = ({ onSelectPrompt }) => {
  const groupedCategories = useMemo(() => {
    return [
      {
        heading: 'Start with a goal',
        intro:
          'Pick a story angle and click any prompt to try it in Search. These queries are ready to use.',
        categories: HOW_IT_WORKS,
      },
      {
        heading: 'More inspiration',
        intro: 'Keep exploring with curated prompts spanning mood, arcs, themes, and more.',
        categories: DEFAULT_PROMPT_CATEGORIES,
      },
    ];
  }, []);

  return (
    <div className="space-y-6 sm:space-y-10">
      <header className="rounded-xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 p-4 sm:p-6 text-white shadow-lg">
        <h1 className="text-xl sm:text-2xl font-semibold">Explore Buffy Episodes</h1>
        <p className="mt-2 max-w-2xl text-xs sm:text-sm text-indigo-100">
          Discover what's possible. Browse sample queries, explore themes, and get inspired. Click any prompt to try it in Search.
        </p>
      </header>

      {/* Tips section moved to top */}
      <div className="rounded-lg border-2 border-blue-200 bg-blue-50/50 p-4 sm:p-6 text-xs sm:text-sm text-gray-700 shadow-sm">
        <h2 className="text-sm sm:text-base font-semibold text-blue-900 mb-3 flex items-center gap-2">
          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          Tips
        </h2>
        <ul className="space-y-2 list-disc pl-4 sm:pl-5 text-gray-700">
          <li>Combine keywords to mix moods and characters, e.g., "Spike redemption episodes with musical elements."</li>
          <li>Click any prompt below to try it in Search and see results across all seasons.</li>
          <li>Use Timeline view in Search to see multi-episode arcs chronologically.</li>
        </ul>
      </div>

      {/* Suggestion areas - visually distinct */}
      <div className="space-y-6 sm:space-y-8">
        {groupedCategories.map(({ heading, intro, categories }) => (
          <section key={heading} className="rounded-lg border border-gray-200 bg-gray-50/30 p-4 sm:p-6">
            <PromptExamples
              heading={heading}
              intro={intro}
              categories={categories}
              layout="grid"
              onSelectPrompt={onSelectPrompt}
            />
          </section>
        ))}
      </div>
    </div>
  );
};
