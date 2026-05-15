import { useMemo, useState } from "react";
import fs from "fs";
import path from "path";
import Link from "next/link";

interface Card {
  id: number;
  name: string;
  pokemon: string;
  aesthetic: number;
  ip: number;
  narrative: number;
  pop_mult: number;
  composite: number;
  signal: string;
  signal_label: string;
  reason: string;
  avg_price_30d: number;
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

export default function Home({ cards }: { cards: Card[] }) {
  const [sortKey, setSortKey] = useState<string>("composite");
  const [filterPokemon, setFilterPokemon] = useState("");
  const [filterSignal, setFilterSignal] = useState("");

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
    list.sort((a, b) => {
      const ak = a[sortKey as keyof Card] as number;
      const bk = b[sortKey as keyof Card] as number;
      return (bk || 0) - (ak || 0);
    });
    return list;
  }, [cards, sortKey, filterPokemon, filterSignal]);

  const uniquePokemon = [...new Set(cards.map((c) => c.pokemon).filter(Boolean))].sort();

  return (
    <div className="min-h-screen p-6 max-w-6xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">PTCG Scout</h1>
        <p className="text-gray-400 mt-2">
          宝可梦卡牌潜力榜 TOP 30 · Updated daily
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
          <option value="price_change_pct">30天涨幅</option>
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

        <div className="ml-auto text-sm text-gray-500 self-center">
          {sorted.length} cards
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sorted.map((card) => (
          <Link
            key={card.id}
            href={`/card/${card.id}`}
            className="block bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-semibold text-sm truncate flex-1 mr-2">
                {card.name}
              </h3>
              <span className="text-lg font-bold tabular-nums">
                {card.composite.toFixed(0)}
              </span>
            </div>
            <div className="text-xs text-gray-500 mb-2">{card.pokemon}</div>
            <div className="flex gap-2 text-xs mb-2">
              <span className="bg-gray-800 px-2 py-0.5 rounded">IP {card.ip.toFixed(0)}</span>
              <span className="bg-gray-800 px-2 py-0.5 rounded">审美 {card.aesthetic.toFixed(0)}</span>
              <span className="bg-gray-800 px-2 py-0.5 rounded">Pop×{card.pop_mult.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className={SIGNAL_COLORS[card.signal] || "text-gray-400"}>
                {card.signal_label}
              </span>
              <span className="text-gray-500">
                ${card.avg_price_30d.toFixed(2)}
                <span className={card.price_change_pct >= 0 ? "text-green-400 ml-1" : "text-red-400 ml-1"}>
                  {card.price_change_pct >= 0 ? "+" : ""}{card.price_change_pct.toFixed(1)}%
                </span>
              </span>
            </div>
          </Link>
        ))}
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
