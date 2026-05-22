"use client";

import { AlertTriangle, TrendingDown, TrendingUp } from "lucide-react";

interface AlertEntry {
  reading: number;
  alert_type: string;
  message: string;
  logged_at: string;
}

interface Props {
  alerts: AlertEntry[];
}

function formatDateTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString([], {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function AlertsHistory({ alerts }: Props) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl border border-red-100 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border-b border-red-100">
        <AlertTriangle className="w-4 h-4 text-red-500" />
        <p className="text-sm font-bold text-red-700">Critical Alert History</p>
        <span className="ml-auto text-xs bg-red-100 text-red-600 font-bold
                         rounded-full px-2 py-0.5">
          {alerts.length} event{alerts.length > 1 ? "s" : ""}
        </span>
      </div>

      {/* Alert list */}
      <div className="divide-y divide-gray-50 max-h-64 overflow-y-auto">
        {alerts.map((alert, i) => {
          const isLow = alert.alert_type === "CRITICAL_LOW";
          return (
            <div key={i} className="flex items-start gap-3 px-4 py-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center
                               flex-shrink-0 mt-0.5
                               ${isLow ? "bg-blue-50" : "bg-red-50"}`}>
                {isLow
                  ? <TrendingDown className="w-4 h-4 text-blue-500" />
                  : <TrendingUp   className="w-4 h-4 text-red-500"  />
                }
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`text-xs font-bold
                    ${isLow ? "text-blue-600" : "text-red-600"}`}>
                    {isLow ? "Critically Low" : "Critically High"}
                  </span>
                  <span className="text-xs font-black text-gray-800">
                    {alert.reading} mg/dL
                  </span>
                </div>
                <p className="text-xs text-gray-400">{formatDateTime(alert.logged_at)}</p>
              </div>
              <div className={`text-xs font-bold px-2 py-1 rounded-full flex-shrink-0
                ${isLow
                  ? "bg-blue-50 text-blue-600"
                  : "bg-red-50 text-red-600"}`}>
                {alert.reading} mg/dL
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}