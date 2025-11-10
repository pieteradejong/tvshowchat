import { FC, useMemo } from 'react';
import { PromptExamples, PromptCategory, DEFAULT_PROMPT_CATEGORIES } from './PromptExamples';

interface UseCasesProps {
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

export const UseCases: FC<UseCasesProps> = ({ onSelectPrompt }) => {
  const groupedCategories = useMemo(() => {
    return [
      {
        heading: 'Start with a goal',
        intro:
          'Pick a story angle and we will prompt you with ready-to-run queries. Use these to jump straight into the search or chat tabs.',
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
    <div className="space-y-10">
      <header className="rounded-xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 p-6 text-white shadow-lg">
        <h1 className="text-2xl font-semibold">Buffy Use Cases & Prompt Library</h1>
        <p className="mt-2 max-w-2xl text-sm text-indigo-100">
          Browse curated scenarios to kickstart semantic search or chat. Click any prompt to copy it, then
          paste into the Search or Chat tab—or keep this page open alongside your discovery session.
        </p>
      </header>

      {groupedCategories.map(({ heading, intro, categories }) => (
        <section key={heading}>
          <PromptExamples
            heading={heading}
            intro={intro}
            categories={categories}
            layout="grid"
            onSelectPrompt={onSelectPrompt}
          />
        </section>
      ))}

      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-6 text-sm text-gray-600">
        <h2 className="text-base font-semibold text-gray-900">Tips</h2>
        <ul className="mt-3 space-y-2 list-disc pl-5">
          <li>Combine keywords to mix moods and characters, e.g., "Spike redemption episodes with musical elements."</li>
          <li>Ask follow-up questions in Chat to refine character arcs or compare themes across seasons.</li>
          <li>Use Search to gather a list, then paste the same prompt into Chat for a quick summary of top results.</li>
        </ul>
      </div>
    </div>
  );
};
