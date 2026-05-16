# Frontend Design Rules

## Stack
- Next.js 14 with `output: "export"` (static HTML/CSS/JS → GitHub Pages)
- Tailwind CSS 3 via PostCSS
- Recharts for charts (RadarChart, LineChart)
- TypeScript strict mode

## Visual System
- **Light theme**: warm cream gradient background (`#fefce8` → `#f0f9ff` → `#fdf2f8`)
- **Glassmorphism**: `backdrop-blur(20px)` on `bg-white/60` with `border-white/80`
- **Typography**: `Playfair Display` for headings, `DM Sans` for body/data
- **Gradients**: gold/amber for high scores, indigo for mid, rose for negative
- **Animated orbs**: large radial-gradient circles with `transform` keyframes for atmosphere

## Layout Rules
- Main grid: `grid-template-columns: repeat(5, 1fr)` with responsive breakpoints (4→3→2)
- Hero card: full-width gradient-border card above the grid, showing #1 card
- Max container width: `max-w-[1600px]` to support 5 columns
- Card aspect-ratio for images: `aspect-[2.5/3.5]` (standard TCG ratio)

## Component Patterns
- **Cards**: `glass-card` class with hover lift (`translateY(-2px)`) and amber border glow
- **Filters**: pill buttons in `bg-white/60` container, active state = dark bg + white text
- **Stagger animation**: `.stagger-item` with `animation-delay` based on index modulo
- **Images**: `object-contain` inside flex-centered container, hover scale(1.1)

## Data Flow
- All pages use `getStaticProps` reading from `path.join(process.cwd(), "..", "data", "cards.json")`
- Dynamic routes: `[id].tsx` with `getStaticPaths` from the same JSON
- No runtime API calls — everything is build-time static
