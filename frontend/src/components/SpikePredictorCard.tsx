"use client";

interface SpikePrediction {
  spike_risk?: "LOW" | "MEDIUM" | "HIGH";
  risk_score?: number;
  reason?: string;
  peak_estimate_mg_dl?: number;
  time_to_peak_minutes?: number;
  actions?: string[];
  foods_of_concern?: string[];
  safer_swap?: string;
  meal?: string;
  latest_cgm?: number;
  parse_error?: boolean;
  raw?: string;
}

interface Props {
  prediction: SpikePrediction | null;
  loading: boolean;
}

export default function SpikePredictorCard({ prediction, loading }: Props) {

  if (loading) {
    return (
      <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-5 animate-pulse space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gray-100" />
          <div className="space-y-1 flex-1">
            <div className="h-3 bg-gray-100 rounded w-40" />
            <div className="h-2 bg-gray-100 rounded w-24" />
          </div>
          <div className="w-16 h-6 bg-gray-100 rounded-full" />
        </div>
        <div className="h-2 bg-gray-100 rounded-full w-full" />
        <div className="grid grid-cols-2 gap-2">
          <div className="h-14 bg-gray-100 rounded-xl" />
          <div className="h-14 bg-gray-100 rounded-xl" />
        </div>
        <div className="space-y-2">
          <div className="h-2 bg-gray-100 rounded w-3/4" />
          <div className="h-2 bg-gray-100 rounded w-1/2" />
        </div>
      </div>
    );
  }

  if (!prediction) return null;

  // If JSON failed, try to extract key info from raw text
  if (prediction.parse_error) {
    const raw = prediction.raw || "";
    const riskMatch = raw.match(/"spike_risk"\s*:\s*"(\w+)"/);
    const reasonMatch = raw.match(/"reason"\s*:\s*"([^"]+)"/);
    const actionsMatch = [...raw.matchAll(/"([^"]{10,100})"/g)].map(m => m[1]).filter(a =>
      !["spike_risk","risk_score","reason","peak_estimate_mg_dl","time_to_peak_minutes",
        "actions","foods_of_concern","safer_swap","HIGH","MEDIUM","LOW"].includes(a)
    ).slice(0, 3);

    const risk = (riskMatch?.[1] || "MEDIUM") as "LOW"|"MEDIUM"|"HIGH";
    const reason = reasonMatch?.[1] || "Spike risk assessed based on meal composition.";

    return (
      <SpikePredictorCard
        loading={false}
        prediction={{
          spike_risk: risk,
          risk_score: risk === "HIGH" ? 8 : risk === "MEDIUM" ? 5 : 2,
          reason,
          actions: actionsMatch.length > 0 ? actionsMatch : ["Monitor your glucose closely after this meal."],
          meal: prediction.meal,
          latest_cgm: prediction.latest_cgm,
        }}
      />
    );
  }

  const risk  = prediction.spike_risk || "LOW";
  const score = Math.min(10, Math.max(1, prediction.risk_score || 1));

  const cfg = {
    LOW:    { emoji: "🟢", label: "Low Risk",    bg: "bg-emerald-50",  border: "border-emerald-200", badge: "bg-emerald-100 text-emerald-700", bar: "bg-emerald-400", text: "text-emerald-700", circle: "bg-emerald-100" },
    MEDIUM: { emoji: "🟡", label: "Medium Risk", bg: "bg-amber-50",    border: "border-amber-200",   badge: "bg-amber-100 text-amber-700",    bar: "bg-amber-400",   text: "text-amber-700",   circle: "bg-amber-100"   },
    HIGH:   { emoji: "🔴", label: "High Risk",   bg: "bg-red-50",      border: "border-red-200",     badge: "bg-red-100 text-red-700",        bar: "bg-red-500",     text: "text-red-700",     circle: "bg-red-100"     },
  }[risk];

  return (
    <div className={`rounded-2xl border ${cfg.border} ${cfg.bg} shadow-sm overflow-hidden`}>

      {/* Header */}
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full ${cfg.circle} flex items-center justify-center text-xl`}>
              ⚡
            </div>
            <div>
              <p className="text-sm font-bold text-gray-800">Glucose Spike Predictor</p>
              {prediction.meal && (
                <p className="text-xs text-gray-400 truncate max-w-[180px]">
                  &ldquo;{prediction.meal}&rdquo;
                </p>
              )}
            </div>
          </div>
          <span className={`text-xs font-bold px-3 py-1 rounded-full ${cfg.badge}`}>
            {cfg.emoji} {cfg.label}
          </span>
        </div>

        {/* Score bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-500">
            <span>Spike Risk Score</span>
            <span className="font-bold">{score} / 10</span>
          </div>
          <div className="w-full h-2.5 bg-white rounded-full border border-gray-200">
            <div
              className={`h-2.5 rounded-full transition-all duration-700 ${cfg.bar}`}
              style={{ width: `${score * 10}%` }}
            />
          </div>
        </div>
      </div>

      {/* Reason */}
      {prediction.reason && (
        <div className="px-5 pb-4">
          <p className="text-xs text-gray-600 leading-relaxed bg-white rounded-xl px-3 py-2 border border-gray-100">
            💬 {prediction.reason}
          </p>
        </div>
      )}

      {/* Stats */}
      {(prediction.peak_estimate_mg_dl || prediction.time_to_peak_minutes) && (
        <div className="px-5 pb-4 grid grid-cols-2 gap-3">
          {prediction.peak_estimate_mg_dl !== undefined && (
            <div className="bg-white rounded-xl px-4 py-3 border border-gray-100 text-center">
              <p className={`text-xl font-black ${cfg.text}`}>
                +{prediction.peak_estimate_mg_dl}
              </p>
              <p className="text-[10px] text-gray-400 font-medium">mg/dL estimated rise</p>
            </div>
          )}
          {prediction.time_to_peak_minutes !== undefined && (
            <div className="bg-white rounded-xl px-4 py-3 border border-gray-100 text-center">
              <p className={`text-xl font-black ${cfg.text}`}>
                {prediction.time_to_peak_minutes}
              </p>
              <p className="text-[10px] text-gray-400 font-medium">min to peak glucose</p>
            </div>
          )}
        </div>
      )}

      {/* Foods of concern */}
      {prediction.foods_of_concern && prediction.foods_of_concern.length > 0 && (
        <div className="px-5 pb-4">
          <p className="text-xs font-semibold text-gray-500 mb-2">⚠️ Watch out for</p>
          <div className="flex flex-wrap gap-1.5">
            {prediction.foods_of_concern.map((f, i) => (
              <span key={i} className="text-xs bg-white border border-orange-200
                                       text-orange-600 px-2.5 py-1 rounded-full font-medium">
                {f}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      {prediction.actions && prediction.actions.length > 0 && (
        <div className="px-5 pb-4">
          <p className="text-xs font-semibold text-gray-500 mb-2">✅ What to do now</p>
          <div className="space-y-2">
            {prediction.actions.map((action, i) => (
              <div key={i} className="flex items-start gap-2.5 bg-white rounded-xl
                                      px-3 py-2.5 border border-gray-100">
                <span className={`text-xs font-black ${cfg.text} mt-0.5 w-4 flex-shrink-0`}>
                  {i + 1}
                </span>
                <p className="text-xs text-gray-700 leading-relaxed">{action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Safer swap */}
      {prediction.safer_swap && (
        <div className="px-5 pb-5">
          <div className="bg-white rounded-xl px-3 py-2.5 border border-blue-100
                          flex items-start gap-2">
            <span className="text-sm mt-0.5">🔄</span>
            <div>
              <p className="text-[10px] font-semibold text-blue-500 uppercase tracking-wide mb-0.5">
                Smarter Swap
              </p>
              <p className="text-xs text-gray-700">{prediction.safer_swap}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}