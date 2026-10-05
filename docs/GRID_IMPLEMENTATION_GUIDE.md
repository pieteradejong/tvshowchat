# Grid Visualization Implementation Guide

## Episode Counts Per Season
- Season 1: 12 episodes
- Seasons 2-7: 22 episodes each
- **Total: 144 episodes**

The grid should dynamically reflect these counts (not a fixed 7×20).

---

## 1. Master Grid View
**"The Complete Series at a Glance"**

### Implementation Approach

#### Component Structure
```typescript
// frontend/src/components/grid/SeriesGrid.tsx
interface GridCell {
  season: number;
  episode: number;
  episodeId: string;
  title: string;
  logline: string;
  // Metrics for coloring
  quoteCount?: number;
  characterPresence?: number;
  deathCount?: number;
  // ... other metrics
}

interface SeriesGridProps {
  episodes: EpisodeLite[];
  metric?: 'quotes' | 'presence' | 'deaths' | 'themes';
  selectedEpisodeId?: string;
  onEpisodeClick: (episodeId: string) => void;
  onEpisodeHover: (episodeId: string | null) => void;
}
```

#### Grid Layout Algorithm
```typescript
// Calculate grid dimensions
const maxEpisodes = Math.max(...seasonCounts); // 22
const gridCols = maxEpisodes; // Use max for consistent column width

// Each row = one season
// Each cell position = (row, col) where col = episode number - 1
// Empty cells for seasons with fewer episodes (e.g., S1 has 12, so cols 12-21 are empty)

const getCellPosition = (season: number, episode: number) => {
  const row = season - 1; // 0-indexed
  const col = episode - 1; // 0-indexed
  return { row, col };
};
```

#### Visual Design
- **CSS Grid**: Use `display: grid` with `grid-template-columns: repeat(22, 1fr)`
- **Cell sizing**: Fixed width/height (e.g., 40px × 40px) or responsive
- **Color encoding**: Use a color scale (e.g., `d3-scale-chromatic` or custom)
  - White → Yellow → Orange → Red for quote count
  - Light → Dark for presence intensity
- **Empty cells**: Show with `opacity: 0.3` or border-only

#### Data Preparation
```typescript
// Backend: Add endpoint to get grid data with metrics
// GET /api/grid/metrics?type=quotes|presence|deaths

// Frontend: Transform episodes into grid cells
const buildGridCells = (episodes: EpisodeLite[], metric: string) => {
  return episodes.map(ep => ({
    ...ep,
    // Fetch or compute metric value
    metricValue: getMetricValue(ep, metric)
  }));
};
```

#### Interaction
- **Hover**: Show tooltip with episode title, logline, metric value
- **Click**: Navigate to episode detail (update URL hash, scroll to detail panel)
- **Keyboard**: Arrow keys to navigate between cells

#### Tech Stack
- **React** for component
- **CSS Grid** for layout
- **d3-scale** or **chroma-js** for color scales
- **React Tooltip** or custom tooltip component

---

## 2. Arc Visualization Over Grid
**"Story Arcs as Paths Through the Grid"**

### Implementation Approach

#### Data Structure
```typescript
interface Arc {
  id: string;
  name: string;
  type: 'character' | 'villain' | 'relationship' | 'theme';
  episodes: Array<{ season: number; episode: number; importance: number }>;
  color: string;
  theme?: string;
}

// Example: Spike's redemption arc
const spikeArc: Arc = {
  id: 'spike-redemption',
  name: "Spike's Redemption",
  type: 'character',
  episodes: [
    { season: 5, episode: 7, importance: 0.3 },  // Introduction
    { season: 6, episode: 7, importance: 0.8 },  // Musical episode
    { season: 7, episode: 22, importance: 1.0 }  // Finale
  ],
  color: '#dc2626'
};
```

#### Path Drawing Algorithm
```typescript
// Convert episode coordinates to SVG path
const episodesToPath = (arc: Arc, cellSize: number, cellGap: number) => {
  const points = arc.episodes.map(ep => {
    const row = ep.season - 1;
    const col = ep.episode - 1;
    const x = col * (cellSize + cellGap) + cellSize / 2;
    const y = row * (cellSize + cellGap) + cellSize / 2;
    return { x, y, importance: ep.importance };
  });
  
  // Use SVG path with smooth curves (quadratic/cubic bezier)
  // Or use D3 line generator with curve
  return d3.line()
    .curve(d3.curveCardinal)
    .x(d => d.x)
    .y(d => d.y)(points);
};
```

#### Visual Design
- **SVG overlay**: Position absolute over grid, same dimensions
- **Path style**: 
  - `stroke-width` = importance × base width (e.g., 2px to 8px)
  - `stroke` = arc color
  - `stroke-dasharray` for different arc types (solid, dashed, dotted)
- **Path markers**: Arrow heads at end, dots at episode points
- **Opacity**: Lower opacity for less important arcs

#### Arc Detection/Definition
```typescript
// Option 1: Manual definition (start here)
const MANUAL_ARCS: Arc[] = [
  {
    id: 'master-arc-s1',
    name: 'The Master',
    type: 'villain',
    episodes: [
      { season: 1, episode: 1, importance: 0.2 },
      { season: 1, episode: 2, importance: 0.3 },
      { season: 1, episode: 12, importance: 1.0 }
    ],
    color: '#7c3aed'
  },
  // ... more arcs
];

// Option 2: Auto-detect from character arcs data
const detectArcsFromCharacterData = (characterArcs: CharacterArcs) => {
  // Find episodes where character presence spikes
  // Group consecutive episodes with high presence
  // Return as Arc objects
};
```

#### Interaction
- **Arc selector**: Dropdown or checkbox list to show/hide arcs
- **Hover arc**: Highlight path, show arc name and episode list
- **Click arc**: Filter grid to show only arc episodes

#### Tech Stack
- **SVG** for path rendering
- **D3.js** for path generation (`d3-line`, `d3-curve`)
- **React** for component and state management

---

## 3. Quote Density Heatmap
**"Where Are the Most Memorable Lines?"**

### Implementation Approach

#### Data Aggregation
```typescript
// Backend: Aggregate quotes per episode
// GET /api/grid/quotes-density
// Returns: { [episodeId]: quoteCount }

// Frontend: Map to grid cells
const buildQuoteHeatmap = (episodes: EpisodeLite[], quotes: Quote[]) => {
  const quoteCounts = new Map<string, number>();
  
  quotes.forEach(quote => {
    const count = quoteCounts.get(quote.episode_id) || 0;
    quoteCounts.set(quote.episode_id, count + 1);
  });
  
  return episodes.map(ep => ({
    ...ep,
    quoteCount: quoteCounts.get(ep.id) || 0
  }));
};
```

#### Color Scale
```typescript
import { scaleSequential, interpolateYlOrRd } from 'd3-scale';

const maxQuotes = Math.max(...episodes.map(e => e.quoteCount));
const colorScale = scaleSequential(interpolateYlOrRd)
  .domain([0, maxQuotes]);

// Apply to cell background
const cellStyle = {
  backgroundColor: colorScale(episode.quoteCount),
  // Or use CSS custom properties
};
```

#### Visual Design
- **Cell background**: Color intensity = quote count
- **Cell badge**: Small number in corner showing count
- **Hover tooltip**: Show top 3 quotes from that episode
- **Legend**: Color scale showing 0 → max quotes

#### Advanced Features
- **Character filter**: "Show only Buffy quotes" → recalculate heatmap
- **Quote quality**: Weight quotes by character importance or memorability
- **Quote clusters**: Highlight episodes with similar quote themes

#### Tech Stack
- **d3-scale** for color scales
- **React** for component
- **CSS** for cell styling

---

## 4. Character Relationship Matrix Over Time
**"Who Interacts With Whom, When?"**

### Implementation Approach

#### Data Structure
```typescript
interface CharacterInteraction {
  character1: string;
  character2: string;
  episodeId: string;
  season: number;
  episode: number;
  interactionType: 'romance' | 'friendship' | 'enmity' | 'neutral';
  intensity: number; // 0-1
}

// Backend: Compute from character co-appearance + context
// GET /api/grid/character-interactions?char1=Buffy&char2=Spike
```

#### Visualization Options

##### Option A: Layered Grids (Recommended for Start)
```typescript
// One grid per character pair
// Toggle which pairs to show
interface RelationshipGridProps {
  characterPair: [string, string];
  interactions: CharacterInteraction[];
  episodes: EpisodeLite[];
}

const RelationshipGrid: React.FC<RelationshipGridProps> = ({ 
  characterPair, 
  interactions,
  episodes 
}) => {
  // Build interaction map
  const interactionMap = new Map(
    interactions.map(i => [i.episodeId, i])
  );
  
  // Color cells by interaction intensity
  return <SeriesGrid 
    episodes={episodes}
    cellColor={(ep) => {
      const interaction = interactionMap.get(ep.id);
      if (!interaction) return 'transparent';
      return intensityToColor(interaction.intensity, interaction.interactionType);
    }}
  />;
};
```

##### Option B: Overlay Lines
```typescript
// Draw lines connecting episodes where characters interact
const drawInteractionLines = (interactions: CharacterInteraction[]) => {
  // Group by episode sequence
  // Draw SVG lines between consecutive interaction episodes
  // Color by interaction type
};
```

#### Interaction Type Detection
```typescript
// Simple heuristic (can be improved with NLP later)
const detectInteractionType = (
  text: string, 
  char1: string, 
  char2: string
): 'romance' | 'friendship' | 'enmity' | 'neutral' => {
  const lower = text.toLowerCase();
  const romanceKeywords = ['kiss', 'love', 'romance', 'date'];
  const enmityKeywords = ['fight', 'hate', 'enemy', 'attack'];
  const friendshipKeywords = ['friend', 'help', 'support', 'together'];
  
  // Check for keywords in context of both characters
  // Return most likely type
};
```

#### Visual Design
- **Color encoding**:
  - Romance = Pink/Red gradient
  - Friendship = Blue/Green gradient
  - Enmity = Red/Orange gradient
  - Neutral = Gray
- **Intensity**: Opacity or saturation = interaction strength
- **Cell markers**: Icons for relationship milestones (first kiss, breakup, etc.)

#### Tech Stack
- **React** for component
- **SVG** for overlay lines (if using Option B)
- **d3-scale** for color mapping

---

## 5. Character Arc Trajectories
**"Character Journeys Through the Grid"**

### Implementation Approach

#### Data Source
```typescript
// Use existing character arcs data
// GET /api/series/character-arcs
// Returns: { [character]: Array<{ episode_id, presence_score }> }

interface CharacterTrajectory {
  character: string;
  episodes: Array<{
    episodeId: string;
    season: number;
    episode: number;
    presenceScore: number;
    milestone?: 'introduction' | 'major-event' | 'death' | 'departure';
  }>;
  color: string;
}
```

#### Trajectory Line Drawing
```typescript
// Similar to arc paths, but smoother curve through presence scores
const drawTrajectory = (
  trajectory: CharacterTrajectory,
  cellSize: number
) => {
  const points = trajectory.episodes
    .filter(e => e.presenceScore > 0) // Only episodes with presence
    .map(e => ({
      x: (e.episode - 1) * cellSize + cellSize / 2,
      y: (e.season - 1) * cellSize + cellSize / 2,
      score: e.presenceScore
    }));
  
  // Use D3 line with smoothing
  const line = d3.line()
    .curve(d3.curveMonotoneX) // Smooth horizontal progression
    .x(d => d.x)
    .y(d => d.y);
  
  return line(points);
};
```

#### Visual Design
- **Line style**: 
  - Thickness = presence score (normalized)
  - Color = character color
  - Opacity = 0.7 (so grid shows through)
- **Milestone markers**: 
  - Introduction = Green circle
  - Major event = Star
  - Death = Black X
  - Departure = Arrow pointing out
- **Cell highlighting**: Cells with high presence get colored border

#### Multi-Character Overlay
```typescript
// Allow selecting multiple characters
const [selectedCharacters, setSelectedCharacters] = useState<string[]>([]);

// Render trajectory for each selected character
{selectedCharacters.map(char => (
  <TrajectoryLine 
    key={char}
    trajectory={getTrajectory(char)}
    color={getCharacterColor(char)}
  />
))}
```

#### Tech Stack
- **D3.js** for line generation
- **SVG** for rendering
- **React** for component

---

## 6. Multi-Layer Grid Dashboard
**"The Everything View"**

### Implementation Approach

#### Layer System
```typescript
interface GridLayer {
  id: string;
  name: string;
  component: React.ComponentType<LayerProps>;
  opacity: number;
  enabled: boolean;
  zIndex: number;
}

const LAYERS: GridLayer[] = [
  { id: 'base', name: 'Episodes', component: BaseGridLayer, opacity: 1, enabled: true, zIndex: 0 },
  { id: 'arcs', name: 'Story Arcs', component: ArcLayer, opacity: 0.8, enabled: false, zIndex: 1 },
  { id: 'characters', name: 'Character Presence', component: CharacterLayer, opacity: 0.7, enabled: false, zIndex: 2 },
  { id: 'quotes', name: 'Quote Density', component: QuoteLayer, opacity: 0.6, enabled: false, zIndex: 3 },
  { id: 'relationships', name: 'Relationships', component: RelationshipLayer, opacity: 0.7, enabled: false, zIndex: 4 },
  { id: 'themes', name: 'Themes', component: ThemeLayer, opacity: 0.6, enabled: false, zIndex: 5 },
];
```

#### Layer Composition
```typescript
const MultiLayerGrid: React.FC = () => {
  const [layers, setLayers] = useState(LAYERS);
  
  return (
    <div className="relative" style={{ width: '100%', height: '600px' }}>
      {/* Base grid */}
      <BaseGridLayer episodes={episodes} />
      
      {/* Overlay layers */}
      {layers
        .filter(l => l.enabled)
        .sort((a, b) => a.zIndex - b.zIndex)
        .map(layer => (
          <div
            key={layer.id}
            className="absolute inset-0"
            style={{ opacity: layer.opacity, pointerEvents: 'none' }}
          >
            <layer.component episodes={episodes} />
          </div>
        ))}
      
      {/* Layer controls */}
      <LayerControls layers={layers} onUpdate={setLayers} />
    </div>
  );
};
```

#### Layer Controls UI
```typescript
const LayerControls: React.FC<{ layers: GridLayer[], onUpdate: (layers: GridLayer[]) => void }> = 
  ({ layers, onUpdate }) => {
  return (
    <div className="absolute top-4 right-4 bg-white p-4 rounded shadow-lg">
      <h3 className="font-semibold mb-2">Layers</h3>
      {layers.map(layer => (
        <label key={layer.id} className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={layer.enabled}
            onChange={(e) => {
              const updated = layers.map(l => 
                l.id === layer.id ? { ...l, enabled: e.target.checked } : l
              );
              onUpdate(updated);
            }}
          />
          <span>{layer.name}</span>
          {layer.enabled && (
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={layer.opacity}
              onChange={(e) => {
                const updated = layers.map(l =>
                  l.id === layer.id ? { ...l, opacity: parseFloat(e.target.value) } : l
                );
                onUpdate(updated);
              }}
            />
          )}
        </label>
      ))}
    </div>
  );
};
```

#### Tech Stack
- **React** for component composition
- **CSS positioning** (absolute) for layer stacking
- **State management** for layer toggles

---

## 7. Search Results as Grid Highlights
**"Where Are My Search Results?"**

### Implementation Approach

#### Integration with Search
```typescript
// In Search component, when results come back:
const handleSearchResults = (results: SearchResult[]) => {
  // Extract episode IDs from results
  const episodeIds = results.map(r => r.episode_id);
  
  // Pass to grid component
  setHighlightedEpisodes(episodeIds);
  setActiveTab('grid'); // Switch to grid tab
};

// In Grid component:
interface GridProps {
  highlightedEpisodes?: string[]; // Episode IDs to highlight
  highlightColor?: string; // Default: blue
}
```

#### Highlighting Algorithm
```typescript
const GridCell: React.FC<{ 
  episode: EpisodeLite;
  isHighlighted: boolean;
  relevance?: number; // 0-1 from search
}> = ({ episode, isHighlighted, relevance }) => {
  const cellStyle = {
    backgroundColor: isHighlighted 
      ? `rgba(59, 130, 246, ${0.3 + (relevance || 0) * 0.5})` // Blue with intensity
      : 'white',
    border: isHighlighted 
      ? '2px solid rgb(59, 130, 246)'
      : '1px solid #e5e7eb',
    // ... other styles
  };
  
  return <div style={cellStyle}>...</div>;
};
```

#### Result Clustering
```typescript
// Detect if results form patterns (arcs, seasons)
const detectResultPatterns = (episodeIds: string[]) => {
  const episodes = episodeIds.map(id => parseEpisodeId(id));
  
  // Check if results are consecutive (arc pattern)
  const isConsecutive = checkConsecutive(episodes);
  
  // Check if results are in same season
  const seasonGroups = groupBySeason(episodes);
  
  return {
    isArc: isConsecutive,
    seasonClusters: seasonGroups,
    suggestions: generateSuggestions(episodes)
  };
};
```

#### Visual Design
- **Highlight color**: Blue border + semi-transparent fill
- **Relevance intensity**: Darker blue = more relevant
- **Result count badge**: Show number of results in that episode
- **Pattern indicators**: If results form arc, show connecting line

#### Tech Stack
- **React** for component
- **CSS** for highlighting styles

---

## Implementation Priority & Phases

### Phase 1: Foundation (Week 1)
1. ✅ Create `SeriesGrid` base component
2. ✅ Implement dynamic grid layout (12, 22, 22, 22, 22, 22, 22)
3. ✅ Add episode cell rendering with hover/click
4. ✅ Add basic color encoding (single metric)
5. ✅ Add tab to App.tsx

### Phase 2: Core Visualizations (Week 2)
6. ✅ Quote density heatmap
7. ✅ Character presence heatmap
8. ✅ Arc path visualization (manual arcs first)
9. ✅ Search result highlighting

### Phase 3: Advanced Features (Week 3)
10. ✅ Character trajectory lines
11. ✅ Relationship overlays
12. ✅ Multi-layer system
13. ✅ Theme heatmap

### Phase 4: Polish (Week 4)
14. ✅ Arc auto-detection
15. ✅ Interaction type detection
16. ✅ Pattern detection for search results
17. ✅ Performance optimization

---

## Technical Architecture

### Component Structure
```
frontend/src/components/grid/
├── SeriesGrid.tsx           # Main grid component
├── GridCell.tsx             # Individual cell component
├── GridLayers/
│   ├── BaseLayer.tsx       # Episode base layer
│   ├── QuoteLayer.tsx      # Quote density
│   ├── ArcLayer.tsx        # Arc paths
│   ├── CharacterLayer.tsx # Character presence
│   ├── RelationshipLayer.tsx
│   └── ThemeLayer.tsx
├── GridControls.tsx        # Layer toggles, filters
└── GridTooltip.tsx         # Hover tooltip
```

### API Endpoints Needed
```typescript
// New endpoints to add:
GET /api/grid/metrics?type=quotes|presence|deaths
GET /api/grid/quotes-density
GET /api/grid/character-interactions?char1=X&char2=Y
GET /api/grid/arcs                    # Return defined arcs
GET /api/grid/themes                  # Theme distribution
```

### Data Flow
```
1. App loads → Fetch episodes, arcs, quotes
2. Grid component receives data
3. Transform data into grid cells
4. Render grid with CSS Grid
5. Overlay SVG layers for arcs/paths
6. Handle interactions (hover, click, filter)
7. Update URL hash for deep linking
```

---

## Key Design Decisions

1. **Grid Layout**: Use CSS Grid (not flexbox) for precise cell positioning
2. **SVG Overlays**: Use SVG for arcs/paths (not canvas) for better React integration
3. **Color Scales**: Use d3-scale for consistent, perceptually uniform colors
4. **State Management**: Local component state (no Redux needed initially)
5. **Performance**: Virtualize if needed (but 144 cells should be fine)
6. **Responsive**: Fixed size for now (desktop only per requirements)

---

## Dependencies to Add

```json
{
  "d3-scale": "^4.0.2",
  "d3-scale-chromatic": "^3.0.0",
  "d3-shape": "^3.2.0"  // For path generation
}
```

---

## Next Steps

1. Create base `SeriesGrid` component with dynamic layout
2. Add to Experiments tab (or create new "Grid" tab)
3. Implement quote density heatmap as first visualization
4. Test with real data
5. Iterate based on feedback
