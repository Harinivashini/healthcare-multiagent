"use client";

import { useState, useEffect, useRef } from "react";
import { AlertTriangle, Clock, RefreshCw } from "lucide-react";

interface AlertData {
  reading: number;
  level: "CRITICAL_LOW" | "CRITICAL_HIGH";
  title: string;
  clinical: string;
  actions: string[];
  recheck_minutes: number;
}

interface Props {
  alert: AlertData;
  onDismiss: () => void;
}

export default function EmergencyAlert({ alert, onDismiss }: Props) {
  const totalSeconds                    = alert.recheck_minutes * 60;
  const [secondsLeft, setSecondsLeft]   = useState(totalSeconds);
  const [pulse, setPulse]               = useState(true);
  const intervalRef                     = useRef<NodeJS.Timeout | null>(null);

  // Countdown timer
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(intervalRef.current!);
          return 0;
        }
        return s - 1;
      });
    }, 1000);

    // Pulse animation toggle
    const pulseInterval = setInterval(() => setPulse((p) => !p), 800);

    return () => {
      clearInterval(intervalRef.current!);
      clearInterval(pulseInterval);
    };
  }, []);

  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const progress = ((totalSeconds - secondsLeft) / totalSeconds) * 100;

  const isLow  = alert.level === "CRITICAL_LOW";
  const accent = isLow ? "#ef4444" : "#dc2626";

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center"
         style={{ backgroundColor: "rgba(0,0,0,0.85)" }}>

      {/* Animated background pulse */}
      <div
        className="absolute inset-0 transition-opacity duration-700"
        style={{
          backgroundColor: accent,
          opacity: pulse ? 0.12 : 0.05,
        }}
      />

      {/* Alert card */}
      <div className="relative w-full max-w-lg mx-4 bg-white rounded-3xl overflow-hidden shadow-2xl">

        {/* Top red bar */}
        <div className="h-2 w-full" style={{ backgroundColor: accent }} />

        {/* Header */}
        <div className="px-6 pt-6 pb-4 text-center"
             style={{ background: `linear-gradient(135deg, #fff5f5 0%, #ffffff 100%)` }}>
          <div className="flex items-center justify-center mb-3">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center text-3xl
                         transition-transform duration-700"
              style={{
                backgroundColor: "#fee2e2",
                transform: pulse ? "scale(1.1)" : "scale(1.0)",
              }}
            >
              🚨
            </div>
          </div>

          <h2 className="text-lg font-black text-red-700 leading-tight mb-1">
            {alert.title}
          </h2>

          {/* Big reading display */}
          <div className="inline-flex items-baseline gap-1 bg-red-50 border border-red-200
                          rounded-2xl px-5 py-2 mt-2">
            <span className="text-4xl font-black text-red-600">{alert.reading}</span>
            <span className="text-sm text-red-400 font-semibold">mg/dL</span>
          </div>
        </div>

        {/* Clinical explanation */}
        <div className="mx-5 mb-4 bg-red-50 border border-red-100 rounded-2xl px-4 py-3">
          <p className="text-xs text-red-800 leading-relaxed text-center">
            {alert.clinical}
          </p>
        </div>

        {/* Actions */}
        <div className="px-5 mb-4">
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 text-center">
            ⚡ Do this RIGHT NOW
          </p>
          <div className="space-y-2">
            {alert.actions.map((action, i) => (
              <div key={i}
                className="flex items-start gap-3 bg-white border border-gray-100
                           rounded-xl px-4 py-2.5 shadow-sm">
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center
                             flex-shrink-0 text-white text-xs font-black mt-0.5"
                  style={{ backgroundColor: accent }}
                >
                  {i + 1}
                </div>
                <p className="text-xs text-gray-700 leading-relaxed">{action}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Countdown timer */}
        {secondsLeft > 0 && (
          <div className="px-5 mb-4">
            <div className="bg-gray-50 border border-gray-100 rounded-2xl p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <span className="text-xs font-semibold text-gray-600">
                    Recheck glucose in
                  </span>
                </div>
                <span className="text-lg font-black text-gray-800 tabular-nums">
                  {String(mins).padStart(2, "0")}:{String(secs).padStart(2, "0")}
                </span>
              </div>
              {/* Progress bar */}
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${progress}%`, backgroundColor: accent }}
                />
              </div>
            </div>
          </div>
        )}

        {secondsLeft === 0 && (
          <div className="px-5 mb-4">
            <div className="bg-red-50 border border-red-200 rounded-2xl px-4 py-3 text-center">
              <p className="text-xs font-bold text-red-700">
                ⏰ Time to recheck! Log your next CGM reading now.
              </p>
            </div>
          </div>
        )}

        {/* Dismiss button */}
        <div className="px-5 pb-6">
          <button
            onClick={onDismiss}
            className="w-full py-3.5 rounded-2xl text-sm font-bold text-white
                       flex items-center justify-center gap-2 transition-all
                       hover:opacity-90 active:scale-95"
            style={{ backgroundColor: accent }}
          >
            <RefreshCw className="w-4 h-4" />
            I understand — Log next reading
          </button>
          <p className="text-center text-xs text-gray-400 mt-2">
            This alert has been recorded in your health history
          </p>
        </div>
      </div>
    </div>
  );
}