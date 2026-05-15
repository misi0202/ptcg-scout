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

  const filtered = filter
    ? boxes.filter((b) => b.name.includes(filter) || b.set_name.includes(filter))
    : boxes;

  return (
    <div className="min-h-screen p-6 max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">卡盒追踪</h1>
        <p className="text-gray-400 mt-2">监测卡盒低点信号</p>
      </header>

      <input
        type="text"
        placeholder="搜索卡盒..."
        className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm w-full max-w-sm mb-6"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />

      <div className="space-y-3">
        {filtered.map((box) => (
          <div
            key={box.id}
            className={`bg-gray-900 border rounded-lg p-4 ${
              box.low_point_alert ? "border-yellow-600" : "border-gray-800"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">{box.name}</h3>
                <p className="text-xs text-gray-500">{box.set_name}</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold">${box.current_price.toFixed(2)}</div>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  box.low_point_alert
                    ? "bg-yellow-900 text-yellow-400"
                    : "bg-gray-800 text-gray-400"
                }`}>
                  {box.low_point_alert ? "低点信号" : box.reprint_status || "正常"}
                </span>
              </div>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <p className="text-gray-500 text-center py-12">暂无数据</p>
        )}
      </div>
    </div>
  );
}

export async function getStaticProps() {
  const dataPath = path.join(process.cwd(), "..", "data", "boxes.json");
  let boxes: Box[] = [];
  try {
    boxes = JSON.parse(fs.readFileSync(dataPath, "utf-8"));
  } catch {
    // no data
  }
  return { props: { boxes } };
}
