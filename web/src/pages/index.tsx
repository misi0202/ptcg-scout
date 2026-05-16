import { useMemo, useState } from "react";
import fs from "fs";
import path from "path";
import Link from "next/link";

interface Card {
  id: number;
  name: string;
  pokemon: string;
  image_url: string;
  rarity: string;
  artist: string;
  set_name: string;
  game: string;
  aesthetic: number;
  ip: number;
  narrative: number;
  pop_mult: number;
  composite: number;
  signal: string;
  signal_label: string;
  reason: string;
  avg_price_30d: number;
  cm_price: number;
  jp_price: number;
  us_price: number;
  price_change_pct: number;
}

const SIGNAL_COLORS: Record<string, string> = {
  bullish: "text-emerald-600",
  cautious: "text-amber-600",
  bearish: "text-rose-600",
  watch: "text-sky-600",
  neutral: "text-stone-500",
  insufficient_data: "text-stone-400",
};

const SIGNAL_BG: Record<string, string> = {
  bullish: "bg-emerald-50 border-emerald-200",
  cautious: "bg-amber-50 border-amber-200",
  bearish: "bg-rose-50 border-rose-200",
  watch: "bg-sky-50 border-sky-200",
  neutral: "bg-stone-50 border-stone-200",
  insufficient_data: "bg-stone-50 border-stone-200",
};

const MARKET_LABELS: Record<string, string> = {
  us: "US",
  eu: "EU",
  jp: "JP",
};

export default function Home({ cards }: { cards: Card[] }) {
  const [filterGame, setFilterGame] = useState("all");
  const [market, setMarket] = useState<"us" | "eu" | "jp">("us");

  const sorted = useMemo(() => {
    let list = [...cards];
    if (filterGame !== "all") {
      list = list.filter((c) => c.game === filterGame);
    }
    return list;
  }, [cards, filterGame]);

  const hero = sorted[0];
  const grid = sorted.slice(1);

  return (
    <div className="relative z-10 min-h-screen px-4 py-8 max-w-[1600px] mx-auto">
      {/* Header */}
      <header className="mb-10 text-center">
        <h1 className="text-5xl font-bold tracking-tight mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
          PTCG <span className="text-amber-500">Scout</span>
        </h1>
        <p className="text-stone-500 text-sm tracking-wide">
          TOP {cards.length} · Cardmarket Intelligence · Updated Daily
        </p>
      </header>

      {/* Filters */}
      <div className="flex items-center justify-center gap-3 mb-10">
        <div className="flex items-center gap-1 bg-white/60 backdrop-blur rounded-full p-1 border border-white/80 shadow-sm">
          {(["all", "pokemon", "pokemon-jp"] as const).map((g) => (
            <button
              key={g}
              onClick={() => setFilterGame(g)}
              className={`px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-200 ${
                filterGame === g
                  ? "bg-stone-800 text-white shadow-md"
                  : "text-stone-500 hover:text-stone-700"
              }`}
            >
              {g === "all" ? "All" : g === "pokemon" ? "EN" : "JP"}
            </button>
          ))}
        </div>
        <span className="text-stone-300">·</span>
        <div className="flex items-center gap-1 bg-white/60 backdrop-blur rounded-full p-1 border border-white/80 shadow-sm">
          {(["us", "eu", "jp"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMarket(m)}
              className={`px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-200 ${
                market === m
                  ? "bg-stone-800 text-white shadow-md"
                  : "text-stone-500 hover:text-stone-700"
              }`}
            >
              {MARKET_LABELS[m]}
            </button>
          ))}
        </div>
        <span className="text-xs text-stone-400 ml-2">{sorted.length} cards</span>
      </div>

      {/* Hero card */}
      {hero && (
        <div className="max-w-5xl mx-auto mb-10">
          <Link href={`/card/${hero.id}`} className="block">
            <div className="gradient-border p-0.5">
              <div className="glass-card rounded-[1.2rem] p-0 flex flex-row overflow-hidden">
                <div className="w-52 shrink-0 bg-stone-50 flex items-center justify-center p-2">
                  {hero.image_url && (
                    <img
                      src={hero.image_url}
                      alt={hero.name}
                      className="w-full h-auto rounded-lg shadow-md transition-transform duration-300 hover:scale-105"
                      loading="eager"
                    />
                  )}
                </div>
                <div className="flex-1 p-6 flex flex-col justify-center">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                      #1
                    </span>
                    <span className="text-xs text-stone-400">{hero.rarity}</span>
                  </div>
                  <h2 className="text-xl font-semibold mb-1" style={{ fontFamily: "'Playfair Display', serif" }}>
                    {hero.name}
                  </h2>
                  <p className="text-sm text-stone-500 mb-3">{hero.set_name} · {hero.artist}</p>
                  <div className="flex items-center gap-4">
                    <div>
                      <span className="text-3xl font-bold score-badge-high bg-clip-text text-transparent bg-gradient-to-r from-amber-500 to-amber-600">
                        {hero.composite.toFixed(0)}
                      </span>
                      <span className="text-xs text-stone-400 ml-1">score</span>
                    </div>
                    <div className="h-8 w-px bg-stone-200" />
                    <div>
                      {market === "jp" && hero.jp_price ? (
                        <span className="text-lg font-semibold">¥{hero.jp_price.toLocaleString()}</span>
                      ) : market === "eu" && hero.cm_price ? (
                        <span className="text-lg font-semibold">€{hero.cm_price.toFixed(2)}</span>
                      ) : hero.avg_price_30d > 0 ? (
                        <span className="text-lg font-semibold">${hero.avg_price_30d.toFixed(2)}</span>
                      ) : hero.us_price > 0 ? (
                        <span className="text-lg font-semibold">${hero.us_price.toFixed(2)}</span>
                      ) : (
                        <span className="text-sm text-stone-400">No price data</span>
                      )}
                      <span className="text-xs text-stone-400 ml-1">{MARKET_LABELS[market]}</span>
                    </div>
                    <div className="h-8 w-px bg-stone-200" />
                    <div className="flex items-center gap-1.5">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${SIGNAL_BG[hero.signal]}`}>
                        {hero.signal_label}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-stone-400 mt-2">{hero.reason}</p>
                </div>
              </div>
            </div>
          </Link>
        </div>
      )}

      {/* Card grid: 5 per row */}
      <div className="card-grid max-w-[1600px] mx-auto">
        {grid.map((card, i) => {
          const price =
            market === "jp" && card.jp_price ? card.jp_price
            : market === "eu" && card.cm_price ? card.cm_price
            : card.avg_price_30d > 0 ? card.avg_price_30d
            : card.us_price;
          const priceLabel = market === "eu" ? "€" : market === "jp" ? "¥" : "$";

          return (
            <Link
              key={card.id}
              href={`/card/${card.id}`}
              className="stagger-item glass-card overflow-hidden flex flex-col group"
              style={{ animationDelay: `${(i % 10) * 60}ms` }}
            >
              <div className="aspect-[2.5/3.5] overflow-hidden bg-stone-50 flex items-center justify-center p-2 group-hover:bg-amber-50/50 transition-colors duration-300">
                {card.image_url ? (
                  <img
                    src={card.image_url}
                    alt={card.name}
                    className="w-full h-full object-contain transition-transform duration-300 group-hover:scale-110"
                    loading="lazy"
                  />
                ) : (
                  <div className="text-stone-300 text-xs">No image</div>
                )}
              </div>
              <div className="p-3 flex-1 flex flex-col">
                <h3 className="text-xs font-semibold line-clamp-2 mb-1 leading-tight">
                  {card.name}
                </h3>
                <p className="text-[10px] text-stone-400 mb-2 line-clamp-1">
                  {card.set_name}
                </p>
                <div className="flex items-center justify-between mt-auto">
                  <span className="text-sm font-bold tabular-nums">
                    {card.composite.toFixed(0)}
                    <span className="text-[10px] text-stone-400 font-normal ml-0.5">pts</span>
                  </span>
                  {price > 0 ? (
                    <span className="text-xs tabular-nums text-stone-600">
                      {priceLabel}{price.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                  ) : (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${SIGNAL_BG[card.signal]} ${SIGNAL_COLORS[card.signal]}`}>
                      {card.signal_label}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      <footer className="mt-16 mb-8 text-center text-xs text-stone-400">
        PTCG Scout · Market data refreshed daily via GitHub Actions · For personal use only
      </footer>
    </div>
  );
}

export async function getStaticProps() {
  const dataPath = path.join(process.cwd(), "..", "data", "cards.json");
  let cards: Card[] = [];
  try {
    const raw = fs.readFileSync(dataPath, "utf-8");
    cards = JSON.parse(raw);
  } catch {
    // no data yet
  }
  return { props: { cards } };
}
