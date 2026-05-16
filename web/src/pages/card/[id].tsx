import fs from "fs";
import path from "path";
import { useRouter } from "next/router";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from "recharts";

interface Card {
  id: number;
  name: string;
  pokemon: string;
  image_url: string;
  rarity: string;
  artist: string;
  set_name: string;
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
  jp_set: string;
  price_change_pct: number;
}

const SIGNAL_STYLES: Record<string, { dot: string; bg: string; border: string; label: string }> = {
  bullish:     { dot: "bg-emerald-500", bg: "bg-emerald-50", border: "border-emerald-200", label: "强烈看涨" },
  cautious:    { dot: "bg-amber-500",   bg: "bg-amber-50",   border: "border-amber-200",   label: "谨慎观望" },
  bearish:     { dot: "bg-rose-500",    bg: "bg-rose-50",    border: "border-rose-200",    label: "规避" },
  watch:       { dot: "bg-sky-500",     bg: "bg-sky-50",     border: "border-sky-200",     label: "关注（可能低点）" },
  neutral:     { dot: "bg-stone-400",   bg: "bg-stone-50",   border: "border-stone-200",   label: "中性" },
  insufficient_data: { dot: "bg-stone-300", bg: "bg-stone-50", border: "border-stone-200", label: "数据不足" },
};

export default function CardDetail({ card, history }: { card: Card | null; history: any[] }) {
  const router = useRouter();

  if (!card) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ fontFamily: "'DM Sans', sans-serif" }}>
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>Card Not Found</h1>
          <button onClick={() => router.push("/")} className="text-amber-600 hover:underline text-sm">← Back</button>
        </div>
      </div>
    );
  }

  const radarData = [
    { name: "IP强度", value: card.ip, fullMark: 100 },
    { name: "审美共识", value: card.aesthetic, fullMark: 100 },
    { name: "叙事价值", value: card.narrative, fullMark: 100 },
    { name: "稀有度", value: ((card.pop_mult - 0.85) / 0.30) * 100, fullMark: 100 },
  ];

  const sig = SIGNAL_STYLES[card.signal] || SIGNAL_STYLES.neutral;
  const priceHistory = history.map((h: any) => ({ date: h.date, price: h.composite }));

  return (
    <div className="min-h-screen px-4 py-8 max-w-5xl mx-auto relative z-10" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      <button onClick={() => router.push("/")} className="text-stone-500 hover:text-amber-600 mb-8 text-sm transition-colors">
        ← Back to rankings
      </button>

      {/* Card header */}
      <div className="flex flex-col md:flex-row gap-8 mb-10">
        <div className="w-56 shrink-0 glass-card p-3 flex items-center justify-center bg-stone-50/50">
          {card.image_url && (
            <img src={card.image_url} alt={card.name} className="w-full rounded-xl shadow-lg" />
          )}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${sig.bg} ${sig.border}`}>
              {sig.label}
            </span>
            <span className="text-xs text-stone-400">{card.rarity}</span>
            <span className="text-xs text-stone-400">{card.set_name}</span>
          </div>
          <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
            {card.name}
          </h1>
          <p className="text-sm text-stone-500 mb-4">{card.artist}</p>

          <div className="flex items-center gap-8 flex-wrap">
            <div>
              <span className="text-4xl font-bold bg-gradient-to-r from-amber-500 to-amber-600 bg-clip-text text-transparent">
                {card.composite.toFixed(0)}
              </span>
              <span className="text-sm text-stone-400 ml-1">composite score</span>
            </div>
            <div className="space-y-1">
              {card.avg_price_30d > 0 && (
                <p className="text-sm text-stone-600">US <span className="font-semibold">${card.avg_price_30d.toFixed(2)}</span></p>
              )}
              {card.cm_price > 0 && (
                <p className="text-sm text-stone-600">EU <span className="font-semibold">€{card.cm_price.toFixed(2)}</span></p>
              )}
              {card.jp_price && (
                <p className="text-sm text-stone-600">JP <span className="font-semibold">¥{card.jp_price.toLocaleString()}</span></p>
              )}
            </div>
          </div>

          <p className="text-xs text-stone-400 mt-3 italic">{card.reason}</p>
        </div>
      </div>

      {/* Detail grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold mb-4 text-stone-600 uppercase tracking-wider" style={{ fontFamily: "'Playfair Display', serif" }}>
            Radar Analysis
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(0,0,0,0.08)" />
              <PolarAngleAxis dataKey="name" tick={{ fill: "#78716c", fontSize: 12 }} />
              <Radar name={card.name} dataKey="value" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold mb-4 text-stone-600 uppercase tracking-wider" style={{ fontFamily: "'Playfair Display', serif" }}>
            Score Breakdown
          </h3>
          <div className="space-y-3">
            {[
              ["IP Strength", card.ip, 100],
              ["Aesthetic", card.aesthetic, 100],
              ["Narrative", card.narrative, 100],
            ].map(([label, val, max]) => (
              <div key={label as string}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-stone-600">{label}</span>
                  <span className="font-semibold">{(val as number).toFixed(0)}</span>
                </div>
                <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-400 to-amber-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, (val as number) / (max as number) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
            <div className="pt-2 border-t border-stone-100">
              <div className="flex justify-between text-sm">
                <span className="text-stone-600">Pop Multiplier</span>
                <span className="font-semibold">×{card.pop_mult.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Price history chart */}
      {priceHistory.length > 1 && (
        <div className="glass-card p-6 mb-10">
          <h3 className="text-sm font-semibold mb-4 text-stone-600 uppercase tracking-wider" style={{ fontFamily: "'Playfair Display', serif" }}>
            Score History
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={priceHistory}>
              <CartesianGrid stroke="rgba(0,0,0,0.04)" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: "#a8a29e", fontSize: 11 }} />
              <YAxis tick={{ fill: "#a8a29e", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "rgba(255,255,255,0.95)", borderRadius: 12, border: "1px solid rgba(0,0,0,0.08)", fontSize: 12 }}
                labelStyle={{ fontWeight: 600 }}
              />
              <Line type="monotone" dataKey="price" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3, fill: "#f59e0b" }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <footer className="text-center text-xs text-stone-400">
        <button onClick={() => router.push("/")} className="hover:text-amber-600 transition-colors">← Back to all cards</button>
      </footer>
    </div>
  );
}

export async function getStaticProps({ params }: { params: { id: string } }) {
  const dataPath = path.join(process.cwd(), "..", "data", "cards.json");
  let card: Card | null = null;
  try {
    const cards: Card[] = JSON.parse(fs.readFileSync(dataPath, "utf-8"));
    card = cards.find((c) => c.id === parseInt(params.id)) || null;
  } catch {}

  const historyDir = path.join(process.cwd(), "..", "data", "history");
  let history: any[] = [];
  try {
    const files = fs.readdirSync(historyDir).sort();
    history = files.map((f) => {
      const content = JSON.parse(fs.readFileSync(path.join(historyDir, f), "utf-8"));
      const entry = content.find((c: any) => c.id === parseInt(params.id));
      return { date: f.replace(".json", ""), composite: entry?.composite || 0 };
    });
  } catch {}

  return { props: { card, history } };
}

export async function getStaticPaths() {
  const dataPath = path.join(process.cwd(), "..", "data", "cards.json");
  try {
    const cards: Card[] = JSON.parse(fs.readFileSync(dataPath, "utf-8"));
    return { paths: cards.map((c) => ({ params: { id: String(c.id) } })), fallback: false };
  } catch {
    return { paths: [], fallback: false };
  }
}
