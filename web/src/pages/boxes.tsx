import fs from "fs";
import path from "path";
import { useState } from "react";

interface Box {
  id: number;
  name: string;
  set_name: string;
  release_date: string;
  reprint_status: string;
  current_price: number;
  low_point_alert: number;
}

export default function Boxes({ boxes }: { boxes: Box[] }) {
  const [filter, setFilter] = useState("");
  const filtered = filter ? boxes.filter((b) => b.name.includes(filter) || b.set_name.includes(filter)) : boxes;

  return (
    <div className="min-h-screen px-4 py-8 max-w-4xl mx-auto relative z-10" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
          Box <span className="text-amber-500">Tracker</span>
        </h1>
        <p className="text-stone-500 text-sm">Reprint alerts & price low points</p>
      </header>

      <input
        type="text"
        placeholder="Search boxes..."
        className="w-full max-w-sm mx-auto block mb-8 px-4 py-2.5 rounded-xl bg-white/60 backdrop-blur border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-300 transition-all"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />

      <div className="space-y-3">
        {filtered.map((box, i) => (
          <div
            key={box.id || i}
            className={`glass-card p-5 flex items-center justify-between stagger-item ${
              box.low_point_alert ? "border-amber-300" : ""
            }`}
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div>
              <h3 className="font-semibold">{box.name}</h3>
              <p className="text-xs text-stone-400">{box.set_name}</p>
            </div>
            <div className="text-right">
              {box.current_price > 0 && (
                <div className="text-lg font-bold">${box.current_price.toFixed(2)}</div>
              )}
              <span className={`text-xs px-2 py-0.5 rounded-full border ${
                box.low_point_alert
                  ? "bg-amber-50 border-amber-200 text-amber-700"
                  : "bg-stone-50 border-stone-200 text-stone-500"
              }`}>
                {box.low_point_alert ? "Low Point Signal" : box.reprint_status}
              </span>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <p className="text-center text-stone-400 py-12">No box data yet</p>
        )}
      </div>
    </div>
  );
}

export async function getStaticProps() {
  const dataPath = path.join(process.cwd(), "..", "data", "boxes.json");
  let boxes: Box[] = [];
  try { boxes = JSON.parse(fs.readFileSync(dataPath, "utf-8")); } catch {}
  return { props: { boxes } };
}
