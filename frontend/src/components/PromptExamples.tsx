import { FC } from 'react';

export interface PromptCategory {
  title: string;
  description?: string;
  icon?: string;
  prompts: string[];
}

interface PromptExamplesProps {
  heading?: string;
  intro?: string;
  categories: PromptCategory[];
  onSelectPrompt?: (prompt: string) => void;
  layout?: 'grid' | 'stacked';
}

export const PromptExamples: FC<PromptExamplesProps> = ({
  heading = 'Need inspiration?',
  intro = 'Try one of these example prompts to explore the Buffy universe.',
  categories,
  onSelectPrompt,
  layout = 'stacked',
}) => {
  if (!categories.length) {
    return null;
  }

  const hasHeading = Boolean(heading && heading.trim().length > 0);
  const hasIntro = Boolean(intro && intro.trim().length > 0);

  return (
    <div className="mt-4 sm:mt-6">
      {(hasHeading || hasIntro) && (
        <div className="mb-3">
          {hasHeading && (
            <h2 className="text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wide">
              {heading}
            </h2>
          )}
          {hasIntro && <p className="text-xs sm:text-sm text-gray-500">{intro}</p>}
        </div>
      )}

      <div
        className={
          layout === 'grid'
            ? 'grid gap-3 sm:gap-4 md:grid-cols-2 xl:grid-cols-3'
            : 'space-y-3 sm:space-y-4'
        }
      >
        {categories.map((category) => {
          const hasHandler = typeof onSelectPrompt === 'function';
          return (
            <section
              key={category.title}
              className="rounded-lg bg-white p-3 sm:p-4 shadow-sm ring-1 ring-gray-200"
            >
              <div className="flex items-center gap-2">
                {category.icon && <span className="text-base sm:text-lg" aria-hidden>{category.icon}</span>}
                <h3 className="text-xs sm:text-sm font-medium text-gray-900">{category.title}</h3>
              </div>
              {category.description && (
                <p className="mt-1 text-xs sm:text-sm text-gray-500">{category.description}</p>
              )}

              <div className="mt-3 flex flex-wrap gap-2">
                {category.prompts.map((prompt) =>
                  hasHandler ? (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => onSelectPrompt?.(prompt)}
                      className="rounded-full border border-blue-200 bg-blue-50 px-3 sm:px-4 py-1 text-xs sm:text-sm text-blue-700 transition hover:border-blue-300 hover:bg-blue-100 break-words"
                    >
                      {prompt}
                    </button>
                  ) : (
                    <span
                      key={prompt}
                      className="rounded-full border border-gray-200 bg-gray-50 px-3 sm:px-4 py-1 text-xs sm:text-sm text-gray-700 break-words"
                    >
                      {prompt}
                    </span>
                  )
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
};

export const DEFAULT_PROMPT_CATEGORIES: PromptCategory[] = [
  {
    title: 'Mood-Based Watching',
    icon: '🌟',
    description: 'Pick an episode that matches tonight’s vibe.',
    prompts: [
      'Comfort episodes after a tough day',
      'Need a spooky Buffy marathon tonight',
      'Lighthearted episodes with music and dancing',
    ],
  },
  {
    title: 'Character Arcs',
    icon: '🧭',
    description: 'Follow multi-episode journeys for your favorite character.',
    prompts: [
      'Series of episodes to watch for Willow’s magic arc',
      'Trace Buffy’s leadership journey across the series',
      'Spike’s redemption episodes in order',
    ],
  },
  {
    title: 'Themes',
    icon: '🧠',
    description: 'Explore recurring ideas and emotional beats.',
    prompts: [
      'Episodes exploring grief and loss',
      'Stories about friendship saving the world',
      'Episodes tackling power and responsibility',
    ],
  },
  {
    title: 'Relationships & Dynamics',
    icon: '💞',
    description: 'Analyze friendships, romances, and rivalries.',
    prompts: [
      'Buffy and Angel relationship milestones',
      'Episodes where the Scoobies clash and reconcile',
      'Faith and Buffy rivalry episodes',
    ],
  },
  {
    title: 'Villains & Foes',
    icon: '👹',
    description: 'Zero in on the Big Bad and famous monster-of-the-week stories.',
    prompts: [
      'Glory focused episodes to watch in order',
      'Mayor Wilkins arc across the series',
      'Iconic monster-of-the-week episodes',
    ],
  },
  {
    title: 'Behind the Scenes',
    icon: '🎬',
    description: 'Dig into production notes, guest stars, and creatives.',
    prompts: [
      'Episodes written by Jane Espenson with standout dialogue',
      'Episodes featuring guest star appearances worth noting',
      'Stories directed by Joss Whedon with dream sequences',
    ],
  },
];
