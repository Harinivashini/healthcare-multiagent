/**
 * components/FoodLogForm.tsx
 * ───────────────────────────
 * Input form for logging a meal / snack.
 */

"use client";

import { useState } from "react";
import { Utensils, Clock } from "lucide-react";

interface Props {
  onSubmit: (description: string, timestamp: string) => void;
  loading: boolean;
}

export default function FoodLogForm({ onSubmit, loading }: Props) {
  const [description, setDescription] = useState("");
  const [timestamp, setTimestamp] = useState("");

  const handleSubmit = () => {
    if (!description.trim()) return;
    onSubmit(description.trim(), timestamp || new Date().toISOString());
    setDescription("");
    setTimestamp("");
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <Utensils className="w-4 h-4 text-brand-600" />
        Log Food Intake
      </h3>

      <textarea
        className="w-full border border-gray-300 rounded-lg p-3 text-sm resize-none
                   focus:outline-none focus:ring-2 focus:ring-brand-500"
        rows={3}
        placeholder="Describe what you ate, e.g. 'grilled chicken with steamed broccoli and brown rice'"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />

      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4 text-gray-400" />
        <input
          type="datetime-local"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm
                     focus:outline-none focus:ring-2 focus:ring-brand-500"
          value={timestamp}
          onChange={(e) => setTimestamp(new Date(e.target.value).toISOString())}
        />
        <span className="text-xs text-gray-400">(optional)</span>
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading || !description.trim()}
        className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50
                   text-white rounded-lg py-2 text-sm font-medium transition-colors"
      >
        {loading ? "Logging…" : "Log Meal"}
      </button>
    </div>
  );
}
