"use client";

interface MacroData {
  carbs_g: number;
  protein_g: number;
  fat_g: number;
  calories_kcal: number;
}

interface MealSlot {
  name: string;
  description: string;
  macros: MacroData;
  prep_tip: string;
}

interface MealPlan {
  goal?: string;
  meals?: {
    breakfast?: MealSlot;
    lunch?: MealSlot;
    dinner?: MealSlot;
  };
  daily_totals?: MacroData;
  clinical_notes?: string;
  raw?: string;
  parse_error?: boolean;
}

interface Props {
  plan: MealPlan;
}

const MEAL_ICONS: Record<string, string> = {
  breakfast: "🌅",
  lunch:     "☀️",
  dinner:    "🌙",
};

function MacroBadge({ label, value, unit }: { label: string; value: any; unit: string }) {
  return (
    <span className="inline-flex flex-col items-center bg-gray-100 rounded px-2 py-1 text-xs">
      <span className="font-semibold text-gray-700">{value ?? "?"}{unit}</span>
      <span className="text-gray-400">{label}</span>
    </span>
  );
}

export default function MealPlanCard({ plan }: Props) {
  if (!plan) return null;

  // Raw text fallback — show as formatted text
  if (plan.parse_error || !plan.meals) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          🥗 Your Meal Plan
        </h3>
        <p className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
          {plan.raw || "No meal plan data available."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {plan.goal && (
        <div className="text-sm text-blue-700 bg-blue-50 rounded-lg px-3 py-2 border border-blue-100">
          🎯 <strong>Goal:</strong> {plan.goal}
        </div>
      )}

      {Object.entries(plan.meals).map(([slot, meal]) => {
        if (!meal) return null;
        return (
          <div key={slot} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{MEAL_ICONS[slot] || "🍽️"}</span>
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide">{slot}</span>
                <h4 className="font-semibold text-gray-800 text-sm">{meal.name}</h4>
              </div>
            </div>
            <p className="text-xs text-gray-600 mb-3">{meal.description}</p>
            {meal.macros && (
              <div className="flex gap-2 flex-wrap mb-2">
                <MacroBadge label="Carbs"   value={meal.macros.carbs_g}       unit="g" />
                <MacroBadge label="Protein" value={meal.macros.protein_g}     unit="g" />
                <MacroBadge label="Fat"     value={meal.macros.fat_g}         unit="g" />
                <MacroBadge label="kcal"    value={meal.macros.calories_kcal} unit=""  />
              </div>
            )}
            {meal.prep_tip && (
              <p className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1">
                💡 {meal.prep_tip}
              </p>
            )}
          </div>
        );
      })}

      {plan.clinical_notes && (
        <div className="bg-red-50 border border-red-100 rounded-lg px-3 py-2 text-xs text-red-700">
          📋 <strong>Clinical notes:</strong> {plan.clinical_notes}
        </div>
      )}
    </div>
  );
}