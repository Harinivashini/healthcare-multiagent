/**
 * components/CGMChart.tsx
 * ────────────────────────
 * Line chart of the last 7 CGM readings using Recharts.
 */

"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend,
} from "recharts";

interface CGMEntry {
  reading: number;
  flagged: boolean;
  logged_at: string;
}

interface Props {
  data: CGMEntry[];
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function CGMChart({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No CGM readings yet. Log a reading to see your trend.
      </div>
    );
  }

  const chartData = [...data].reverse().map((d) => ({
    time: formatTime(d.logged_at),
    glucose: d.reading,
    flagged: d.flagged ? d.reading : null,
  }));

  return (
    <div className="w-full h-56">
      <h3 className="text-sm font-semibold text-gray-600 mb-2">
        Blood Glucose (mg/dL) — Last {data.length} readings
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 11 }} />
          <YAxis domain={[60, 320]} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <ReferenceLine y={80}  stroke="#f59e0b" strokeDasharray="4 4" label={{ value: "Low", fontSize: 10 }} />
          <ReferenceLine y={180} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: "High", fontSize: 10 }} />
          <ReferenceLine y={300} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "Critical", fontSize: 10 }} />
          <Line
            type="monotone"
            dataKey="glucose"
            stroke="#0284c7"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            name="Glucose"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
