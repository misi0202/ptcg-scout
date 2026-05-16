# Frontend
Next.js 14 static export (`output:"export"`) → GitHub Pages. Tailwind 3 + Recharts.

**Visual**: Light warm-gradient bg. Glass cards: `backdrop-blur(20px) bg-white/60 border-white/80`. Fonts: Playfair Display (headings) + DM Sans (body). Gold gradient on high scores, indigo on mid, rose on negative. Floating radial-gradient orbs for atmosphere.

**Layout**: `repeat(5,1fr)` grid → 4→3→2 responsive. Hero card with animated gradient border above grid. `max-w-[1600px]`. Card images: `aspect-[2.5/3.5]`.

**Components**: `.glass-card` with `hover:translateY(-2px)`. Filter pills: `bg-white/60` container, active=`bg-stone-800 text-white`. `.stagger-item` + `animation-delay` from index. Images: `object-contain`, `hover:scale-110`.

**Data**: `getStaticProps` reads `path.join(cwd,"..","data","cards.json")`. Dynamic routes with `getStaticPaths` from same file. No runtime API calls.
