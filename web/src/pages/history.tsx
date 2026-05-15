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
  const [expanded, setExpanded] = useState<string>("");

  return (
    <div className="min-h-screen p-6 max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">历史快照</h1>
        <p className="text-gray-400 mt-2">回溯每日评分快照（最近30天）</p>
      </header>

      <div className="space-y-2">
        {snapshots.map((s) => (
          <div key={s.date}>
            <button
              onClick={() => setExpanded(expanded === s.date ? "" : s.date)}
              className="w-full text-left bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{s.date}</h3>
                  <p className="text-xs text-gray-500">{s.count} cards · TOP: {s.topCard}</p>
                </div>
                <span className="text-gray-500 text-sm">
                  {expanded === s.date ? "收起 ↑" : "展开 →"}
                </span>
              </div>
            </button>

            {expanded === s.date && (
              <div className="bg-gray-900 border border-gray-800 border-t-0 rounded-b-lg p-4 ml-4">
                {s.topCards.map((c, i) => (
                  <div key={i} className="flex justify-between py-1 text-sm">
                    <span className="text-gray-300">{i + 1}. {c.name}</span>
                    <span className="text-gray-400">{c.composite.toFixed(0)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {snapshots.length === 0 && (
          <p className="text-gray-500 text-center py-12">暂无历史快照。数据将在每日运行后累积。</p>
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
          name: c.name || "?",
          composite: c.composite || 0,
        })),
      };
    });
  } catch {
    // no data
  }
  return { props: { snapshots } };
}
