/**
 * components/MealPlanCard.tsx
 * ────────────────────────────
 * Displays the generated meal plan in a clean card layout.
 */

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
  meals: {
    breakfast: MealSlot;
    lunch: MealSlot;
    dinner: MealSlot;
  };
  daily_totals?: MacroData;
  clinical_notes?: string;
}

interface Props {
  plan: MealPlan;
}

const MEAL_ICONS: Record<string, string> = {
  breakfast: "🌅",
  lunch: "☀️",
  dinner: "🌙",
};

function MacroBadge({ label, value, unit }: { label: string; value: number; unit: string }) {
  return (
    <span className="inline-flex flex-col items-center bg-gray-100 rounded px-2 py-1 text-xs">
      <span className="font-semibold text-gray-700">{value ?? "?"}{unit}</span>
      <span className="text-gray-400">{label}</span>
    </span>
  );
}

export default function MealPlanCard({ plan }: Props) {
  if (!plan || !plan.meals) return null;

  return (
    <div className="space-y-4">
      {plan.goal && (
        <p className="text-sm text-brand-700 bg-brand-50 rounded-lg px-3 py-2 border border-brand-100">
          🎯 <strong>Goal:</strong> {plan.goal}
        </p>
      )}

      {Object.entries(plan.meals).map(([slot, meal]) => (
        <div key={slot} className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">{MEAL_ICONS[slot] || "🍽️"}</span>
            <div>
              <span className="text-xs text-gray-400 uppercase tracking-wide">{slot}</span>
              <h4 className="font-semibold text-gray-800 text-sm">{meal.name}</h4>
            </div>
          </div>
          <p className="text-xs text-gray-600 mb-3">{meal.description}</p>
          <div className="flex gap-2 flex-wrap mb-2">
            <MacroBadge label="Carbs"   value={meal.macros?.carbs_g}   unit="g" />
            <MacroBadge label="Protein" value={meal.macros?.protein_g} unit="g" />
            <MacroBadge label="Fat"     value={meal.macros?.fat_g}     unit="g" />
            <MacroBadge label="kcal"    value={meal.macros?.calories_kcal} unit="" />
          </div>
          {meal.prep_tip && (
            <p className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1">
              💡 {meal.prep_tip}
            </p>
          )}
        </div>
      ))}

      {plan.clinical_notes && (
        <div className="bg-red-50 border border-red-100 rounded-lg px-3 py-2 text-xs text-red-700">
          📋 <strong>Clinical notes:</strong> {plan.clinical_notes}
        </div>
      )}
    </div>
  );
}
