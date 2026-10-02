import type { PromptCategory } from './PromptExamples';

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
