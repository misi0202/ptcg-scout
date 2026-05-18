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
  price_signal: number;
  ip_signal: number;
  volume_signal: number;
  momentum: number;
  composite: number;
  divergence_score: number;
  jp_name: string;
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

const MARKET_CONFIG = [
  { key: "us" as const, label: "US", symbol: "$", desc: "TCGPlayer" },
  { key: "eu" as const, label: "EU", symbol: "€", desc: "Cardmarket" },
  { key: "jp" as const, label: "JP", symbol: "¥", desc: "JustTCG" },
  { key: "cny" as const, label: "CNY", symbol: "¥", desc: "汇率换算" },
];

type MarketKey = typeof MARKET_CONFIG[number]["key"];

function toCNY(card: Card): number {
  if (card.jp_price) return Math.round(card.jp_price / 100 * 4.65);
  if (card.cm_price) return Math.round(card.cm_price * 7.85 * 100) / 100;
  const usd = card.avg_price_30d || card.us_price;
  if (usd) return Math.round(usd * 7.24 * 100) / 100;
  return 0;
}

function HeroPrice({ hero, market }: { hero: Card; market: MarketKey }) {
  if (market === "cny") {
    const cny = toCNY(hero);
    return cny > 0 ? (
      <span className="text-lg font-semibold">¥{cny.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
    ) : (
      <span className="text-sm text-stone-400">No data</span>
    );
  }
  if (market === "jp" && hero.jp_price) {
    return <span className="text-lg font-semibold">¥{hero.jp_price.toLocaleString()}</span>;
  }
  if (market === "eu" && hero.cm_price) {
    return <span className="text-lg font-semibold">€{hero.cm_price.toFixed(2)}</span>;
  }
  if (hero.avg_price_30d > 0) {
    return <span className="text-lg font-semibold">${hero.avg_price_30d.toFixed(2)}</span>;
  }
  if (hero.us_price > 0) {
    return <span className="text-lg font-semibold">${hero.us_price.toFixed(2)}</span>;
  }
  return <span className="text-sm text-stone-400">No price data</span>;
}

function getPrice(card: Card, market: MarketKey) {
  if (market === "cny") return { price: toCNY(card), label: "¥" };
  if (market === "jp" && card.jp_price) return { price: card.jp_price, label: "¥" };
  if (market === "eu" && card.cm_price) return { price: card.cm_price, label: "€" };
  const price = card.avg_price_30d > 0 ? card.avg_price_30d : card.us_price;
  return { price, label: "$" };
}

export default function Home({ cards }: { cards: Card[] }) {
  const [filterGame, setFilterGame] = useState("all");
  const [market, setMarket] = useState<MarketKey>("us");
  const [scoreMode, setScoreMode] = useState<"composite" | "divergence">("composite");

  const sorted = useMemo(() => {
    let list = [...cards];
    if (filterGame === "pokemon-jp") {
      list = list.filter((c) => c.game === "pokemon-jp");
    } else if (filterGame === "pokemon") {
      list = list.filter((c) => c.game === "pokemon");
    }
    if (scoreMode === "divergence") {
      list.sort((a, b) => b.divergence_score - a.divergence_score);
    }
    return list;
  }, [cards, filterGame, scoreMode]);

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
      <div className="flex items-center justify-center gap-3 mb-10 flex-wrap">
        {/* Score mode toggle */}
        <span className="text-[10px] text-stone-400 uppercase tracking-wider">评分</span>
        <div className="flex items-center gap-1 bg-white/60 backdrop-blur rounded-full p-1 border border-white/80 shadow-sm">
          <button
            onClick={() => setScoreMode("composite")}
            className={`px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-200 ${
              scoreMode === "composite" ? "bg-stone-800 text-white shadow-md" : "text-stone-500 hover:text-stone-700"
            }`}
          >评分1</button>
          <button
            onClick={() => setScoreMode("divergence")}
            className={`px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-200 ${
              scoreMode === "divergence" ? "bg-amber-500 text-white shadow-md" : "text-stone-500 hover:text-stone-700"
            }`}
          >评分2</button>
        </div>

        <span className="text-stone-300">·</span>

        {/* Game filter */}
        <span className="text-[10px] text-stone-400 uppercase tracking-wider">市场</span>
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

        {/* Price currency toggle */}
        <span className="text-[10px] text-stone-400 uppercase tracking-wider">价格</span>
        <div className="flex items-center gap-1 bg-white/60 backdrop-blur rounded-full p-1 border border-white/80 shadow-sm">
          {MARKET_CONFIG.map((m) => (
            <button
              key={m.key}
              onClick={() => setMarket(m.key)}
              className={`px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-200 ${
                market === m.key
                  ? "bg-stone-800 text-white shadow-md"
                  : "text-stone-500 hover:text-stone-700"
              }`}
            >
              <span>{m.label}</span>
              <span className="ml-1 opacity-50 text-[10px]">{m.desc}</span>
            </button>
          ))}
        </div>

        <span className="text-xs text-stone-400">{sorted.length} cards</span>
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
                    {hero.jp_name || hero.name}
                  </h2>
                  {hero.jp_name && (
                    <p className="text-xs text-stone-400 mb-1">{hero.name}</p>
                  )}
                  <p className="text-sm text-stone-500 mb-3">{hero.set_name} · {hero.artist}</p>
                  <div className="flex items-center gap-4">
                    <div>
                      <span className="text-3xl font-bold score-badge-high bg-clip-text text-transparent bg-gradient-to-r from-amber-500 to-amber-600">
                        {(scoreMode === "divergence" ? hero.divergence_score : hero.composite).toFixed(0)}
                      </span>
                      <span className="text-xs text-stone-400 ml-1">{scoreMode === "divergence" ? "div" : "score"}</span>
                    </div>
                    <div className="h-8 w-px bg-stone-200" />
                    <HeroPrice hero={hero} market={market} />
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
          const { price, label: priceLabel } = getPrice(card, market);

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
                  {card.jp_name || card.name}
                </h3>
                <p className="text-[10px] text-stone-400 mb-2 line-clamp-1">
                  {card.set_name}
                </p>
                <div className="flex items-center justify-between mt-auto">
                  <span className="text-sm font-bold tabular-nums">
                    {(scoreMode === "divergence" ? card.divergence_score : card.composite).toFixed(0)}
                    <span className="text-[10px] text-stone-400 font-normal ml-0.5">{scoreMode === "divergence" ? "div" : "pts"}</span>
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
