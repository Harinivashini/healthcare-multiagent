/**
 * components/MoodChart.tsx
 * ─────────────────────────
 * Bar chart of the last 7 mood scores (1-5 scale).
 */

"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface MoodEntry {
  mood: string;
  score: number;
  logged_at: string;
}

interface Props {
  data: MoodEntry[];
}

const MOOD_COLORS: Record<number, string> = {
  1: "#ef4444",   // sad/angry
  2: "#f97316",   // tired/anxious
  3: "#facc15",   // neutral
  4: "#84cc16",   // content/calm
  5: "#22c55e",   // happy/excited
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

export default function MoodChart({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No mood entries yet. Log your mood to see the trend.
      </div>
    );
  }

  const chartData = [...data].reverse().map((d) => ({
    date: formatDate(d.logged_at),
    score: d.score,
    mood: d.mood,
  }));

  return (
    <div className="w-full h-56">
      <h3 className="text-sm font-semibold text-gray-600 mb-2">
        Mood Score — Last {data.length} sessions
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(value: number, _: string, props: any) => [
              `${value}/5 (${props.payload.mood})`, "Mood Score",
            ]}
          />
          <Bar dataKey="score" radius={[4, 4, 0, 0]} name="Mood Score">
            {chartData.map((entry, idx) => (
              <Cell
                key={`cell-${idx}`}
                fill={MOOD_COLORS[entry.score] || "#94a3b8"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
