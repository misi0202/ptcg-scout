import fs from "fs";
import path from "path";
import { useState } from "react";

interface Snapshot {
  date: string;
  count: number;
  topCard: string;
  topCards: { name: string; composite: number }[];
}

export default function History({ snapshots }: { snapshots: Snapshot[] }) {
  const [expanded, setExpanded] = useState("");

  return (
    <div className="min-h-screen px-4 py-8 max-w-3xl mx-auto relative z-10" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
          History <span className="text-amber-500">Snapshots</span>
        </h1>
        <p className="text-stone-500 text-sm">Last 30 days of card rankings</p>
      </header>

      <div className="space-y-2">
        {snapshots.map((s, i) => (
          <div key={s.date} className="stagger-item" style={{ animationDelay: `${i * 40}ms` }}>
            <button
              onClick={() => setExpanded(expanded === s.date ? "" : s.date)}
              className="w-full text-left glass-card p-4 transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-sm">{s.date}</h3>
                  <p className="text-xs text-stone-400">{s.count} cards · #{s.topCard}</p>
                </div>
                <span className="text-stone-300 text-xs">{expanded === s.date ? "Collapse ↑" : "Expand →"}</span>
              </div>
            </button>

            {expanded === s.date && (
              <div className="glass-card mt-1 p-4 ml-4 rounded-lg">
                {s.topCards.map((c, j) => (
                  <div key={j} className="flex justify-between py-1 text-sm">
                    <span className="text-stone-600">{j + 1}. {c.name}</span>
                    <span className="font-semibold">{c.composite.toFixed(0)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {snapshots.length === 0 && (
          <p className="text-center text-stone-400 py-12">No history yet. Data accumulates after daily runs.</p>
        )}
      </div>
    </div>
  );
}

export async function getStaticProps() {
  const historyDir = path.join(process.cwd(), "..", "data", "history");
  let snapshots: Snapshot[] = [];
  try {
    const files = fs.readdirSync(historyDir).sort().reverse();
    snapshots = files.slice(0, 30).map((f) => {
      const content = JSON.parse(fs.readFileSync(path.join(historyDir, f), "utf-8"));
      return {
        date: f.replace(".json", ""),
        count: content.length,
        topCard: content[0]?.name || "",
        topCards: content.slice(0, 5).map((c: any) => ({
          name: c.name || "?", composite: c.composite || 0,
        })),
      };
    });
  } catch {}
  return { props: { snapshots } };
}
