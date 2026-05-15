import fs from "fs";
import path from "path";
import { useRouter } from "next/router";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface Card {
  id: number;
  name: string;
  pokemon: string;
  image_url: string;
  rarity: string;
  artist: string;
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

export default function CardDetail({ card, history }: { card: Card | null; history: any[] }) {
  const router = useRouter();

  if (!card) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        Card not found · <button onClick={() => router.push("/")} className="underline ml-2">Back</button>
      </div>
    );
  }

  const radarData = [
    { name: "IP强度", value: card.ip, fullMark: 100 },
    { name: "审美共识", value: card.aesthetic, fullMark: 100 },
    { name: "叙事价值", value: card.narrative, fullMark: 100 },
    { name: "稀有度", value: (card.pop_mult - 0.85) / 0.30 * 100, fullMark: 100 },
  ];

  const priceHistory = history.map((h: any) => ({
    date: h.date,
    price: h.composite,
  }));

  return (
    <div className="min-h-screen p-6 max-w-4xl mx-auto">
      <button
        onClick={() => router.push("/")}
        className="text-gray-400 hover:text-white mb-6 text-sm"
      >
        ← Back to rankings
      </button>

      <div className="flex gap-6 mb-8">
        {card.image_url && (
          <div className="w-48 shrink-0">
            <img src={card.image_url} alt={card.name} className="w-full rounded-lg" />
          </div>
        )}
        <div>
          <h1 className="text-2xl font-bold">{card.name}</h1>
          <p className="text-gray-400 text-sm mt-1">{card.rarity} · {card.artist}</p>
          <p className="text-gray-500 text-sm mt-1">{card.pokemon}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">四维雷达图</h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="name" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
              <Radar
                name={card.name}
                dataKey="value"
                stroke="#60A5FA"
                fill="#60A5FA"
                fillOpacity={0.3}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">评分详情</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">综合评分</span>
              <span className="font-bold text-xl">{card.composite.toFixed(0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">IP强度</span>
              <span>{card.ip.toFixed(0)} / 100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">审美共识</span>
              <span>{card.aesthetic.toFixed(0)} / 100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">叙事价值</span>
              <span>{card.narrative.toFixed(0)} / 100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Pop乘数</span>
              <span>×{card.pop_mult.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">趋势信号</span>
              <span className="font-semibold">{card.signal_label}</span>
            </div>
            <hr className="border-gray-800" />
            <div className="flex justify-between">
              <span className="text-gray-400">30日均价</span>
              <span>${card.avg_price_30d.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">月环比</span>
              <span className={card.price_change_pct >= 0 ? "text-green-400" : "text-red-400"}>
                {card.price_change_pct >= 0 ? "+" : ""}{card.price_change_pct.toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">30天成交量</span>
              <span>{card.volume_30d}</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">{card.reason}</p>
          </div>
        </div>
      </div>

      {priceHistory.length > 1 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-8">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">历史评分趋势</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={priceHistory}>
              <CartesianGrid stroke="#374151" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: "#9CA3AF", fontSize: 11 }} />
              <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }}
                labelStyle={{ color: "#F9FAFB" }}
              />
              <Line type="monotone" dataKey="price" stroke="#60A5FA" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export async function getStaticProps({ params }: { params: { id: string } }) {
  const dataPath = path.join(process.cwd(), "..", "data", "cards.json");
  let card: Card | null = null;
  try {
    const raw = fs.readFileSync(dataPath, "utf-8");
    const cards: Card[] = JSON.parse(raw);
    card = cards.find((c) => c.id === parseInt(params.id)) || null;
  } catch {
    // no data
  }

  const historyDir = path.join(process.cwd(), "..", "data", "history");
  let history: any[] = [];
  try {
    const files = fs.readdirSync(historyDir).sort();
    history = files.map((f) => {
      const content = JSON.parse(fs.readFileSync(path.join(historyDir, f), "utf-8"));
      const entry = content.find((c: any) => c.id === parseInt(params.id));
      return { date: f.replace(".json", ""), composite: entry?.composite || 0 };
    });
  } catch {
    // no history
  }

  return { props: { card, history } };
}

export async function getStaticPaths() {
  const dataPath = path.join(process.cwd(), "..", "data", "cards.json");
  try {
    const raw = fs.readFileSync(dataPath, "utf-8");
    const cards: Card[] = JSON.parse(raw);
    const paths = cards.map((c) => ({ params: { id: String(c.id) } }));
    return { paths, fallback: false };
  } catch {
    return { paths: [], fallback: false };
  }
}
