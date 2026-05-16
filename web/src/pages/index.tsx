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
  jp_name: string;
  jp_set: string;
  price_change_pct: number;
  volume_30d: number;
  supply_demand_ratio: number;
}

const SIGNAL_COLORS: Record<string, string> = {
  bullish: "text-green-400",
  cautious: "text-yellow-400",
  bearish: "text-red-400",
  watch: "text-blue-400",
  neutral: "text-gray-400",
  insufficient_data: "text-gray-500",
};

const MARKET_LABELS: Record<string, string> = {
  us: "TCGPlayer",
  eu: "Cardmarket",
  jp: "JP Market",
};

export default function Home({ cards }: { cards: Card[] }) {
  const [sortKey, setSortKey] = useState<string>("composite");
  const [filterPokemon, setFilterPokemon] = useState("");
  const [filterSignal, setFilterSignal] = useState("");
  const [filterGame, setFilterGame] = useState<string>("all");
  const [market, setMarket] = useState<"us" | "eu" | "jp">("us");

  const sorted = useMemo(() => {
    let list = [...cards];
    if (filterPokemon) {
      list = list.filter((c) =>
        c.pokemon.toLowerCase().includes(filterPokemon.toLowerCase())
      );
    }
    if (filterSignal) {
      list = list.filter((c) => c.signal === filterSignal);
    }
    if (filterGame !== "all") {
      list = list.filter((c) => c.game === filterGame);
    }
    list.sort((a, b) => {
      const ak = a[sortKey as keyof Card] as number;
      const bk = b[sortKey as keyof Card] as number;
      return (bk || 0) - (ak || 0);
    });
    return list;
  }, [cards, sortKey, filterPokemon, filterSignal, filterGame]);

  const uniquePokemon = [...new Set(cards.map((c) => c.pokemon).filter(Boolean))].sort();

  return (
    <div className="min-h-screen p-6 max-w-6xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">PTCG Scout</h1>
        <p className="text-gray-400 mt-2">
          宝可梦卡牌潜力榜 TOP 50 · Updated daily
        </p>
      </header>

      <div className="flex flex-wrap gap-4 mb-6">
        <select
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value)}
        >
          <option value="composite">综合分</option>
          <option value="ip">IP强度</option>
          <option value="aesthetic">审美共识</option>
          <option value="narrative">叙事价值</option>
          <option value="pop_mult">稀有度</option>
          <option value="avg_price_30d">均价</option>
        </select>

        <select
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
          value={filterPokemon}
          onChange={(e) => setFilterPokemon(e.target.value)}
        >
          <option value="">全部宝可梦</option>
          {uniquePokemon.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <select
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
          value={filterSignal}
          onChange={(e) => setFilterSignal(e.target.value)}
        >
          <option value="">全部信号</option>
          <option value="bullish">🟢 强烈看涨</option>
          <option value="cautious">🟡 谨慎观望</option>
          <option value="bearish">🔴 规避</option>
          <option value="watch">🔵 关注</option>
        </select>

        <div className="flex items-center gap-2 ml-auto">
          <span className="text-xs text-gray-500">Region:</span>
          {(["all", "pokemon", "pokemon-jp"] as const).map((g) => (
            <button
              key={g}
              onClick={() => setFilterGame(g)}
              className={`px-3 py-1.5 text-xs rounded border transition-colors ${
                filterGame === g
                  ? "bg-blue-600 border-blue-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600"
              }`}
            >
              {g === "all" ? "All" : g === "pokemon" ? "EN" : "JP"}
            </button>
          ))}
          <span className="text-xs text-gray-600 mx-2">|</span>
          <span className="text-xs text-gray-500">Price:</span>
          {(["us", "eu", "jp"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMarket(m)}
              className={`px-3 py-1.5 text-xs rounded border transition-colors ${
                market === m
                  ? "bg-blue-600 border-blue-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600"
              }`}
            >
              {MARKET_LABELS[m]}
            </button>
          ))}
          <span className="text-xs text-gray-600 ml-2">{sorted.length} cards</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sorted.map((card) => {
          const price =
            market === "jp" && card.jp_price ? card.jp_price
            : market === "eu" && card.cm_price ? card.cm_price
            : card.avg_price_30d;
          const priceLabel = market === "eu" ? "€" : market === "jp" ? "¥" : "$";
          return (
            <Link
              key={card.id}
              href={`/card/${card.id}`}
              className="block bg-gray-900 border border-gray-800 rounded-lg overflow-hidden hover:border-gray-700 transition-colors"
            >
              {card.image_url && (
                <div className="aspect-[2.5/3.5] overflow-hidden bg-gray-800">
                  <img
                    src={card.image_url}
                    alt={card.name}
                    className="w-full h-full object-contain"
                    loading="lazy"
                  />
                </div>
              )}
              <div className="p-4">
                <div className="flex items-start justify-between mb-1">
                  <h3 className="font-semibold text-sm truncate flex-1 mr-2">
                    {card.name}
                  </h3>
                  <span className="text-lg font-bold tabular-nums shrink-0">
                    {card.composite.toFixed(0)}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mb-2">{card.set_name} · {card.rarity}</div>
                <div className="flex gap-2 text-xs mb-2">
                  <span className="bg-gray-800 px-2 py-0.5 rounded">IP {card.ip.toFixed(0)}</span>
                  <span className="bg-gray-800 px-2 py-0.5 rounded">美 {card.aesthetic.toFixed(0)}</span>
                  <span className="bg-gray-800 px-2 py-0.5 rounded">叙 {card.narrative.toFixed(0)}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className={SIGNAL_COLORS[card.signal] || "text-gray-400"}>
                    {card.signal_label}
                  </span>
                  <span className="text-gray-500">
                    {priceLabel}{price.toFixed(2)}
                  </span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      <footer className="mt-12 text-center text-xs text-gray-600">
        PTCG Scout · Data refreshed daily via GitHub Actions · For personal use only
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
