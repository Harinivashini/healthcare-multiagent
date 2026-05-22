"use client";

import { useState } from "react";
import { RefreshCw, BookOpen, X, Clock, Users, ChefHat } from "lucide-react";

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

interface Recipe {
  meal_name?: string;
  servings?: number;
  prep_time_minutes?: number;
  cook_time_minutes?: number;
  ingredients?: { item: string; amount: string; unit: string }[];
  steps?: string[];
  health_tip?: string;
  parse_error?: boolean;
  raw?: string;
}

interface MealPlan {
  goal?: string;
  meals?: { breakfast?: MealSlot; lunch?: MealSlot; dinner?: MealSlot };
  clinical_notes?: string;
  raw?: string;
  parse_error?: boolean;
}

interface Props {
  plan: MealPlan;
  userId: number;
  onSwap: (slot: string, currentMealName: string) => Promise<MealSlot | null>;
  onRecipe: (mealName: string) => Promise<Recipe | null>;
}

const MEAL_ICONS: Record<string, string> = {
  breakfast: "🌅",
  lunch:     "☀️",
  dinner:    "🌙",
};

// ── Recipe Modal ──────────────────────────────────────────────────────────────

function RecipeModal({ recipe, mealName, onClose }: {
  recipe: Recipe;
  mealName: string;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
         style={{ backgroundColor: "rgba(0,0,0,0.5)" }}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh]
                      overflow-hidden flex flex-col">

        {/* Modal header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <ChefHat className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-sm font-bold text-gray-800">
                {recipe.meal_name || mealName}
              </p>
              <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
                {recipe.servings && (
                  <span className="flex items-center gap-1">
                    <Users className="w-3 h-3" /> {recipe.servings} serving
                  </span>
                )}
                {recipe.prep_time_minutes && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Prep {recipe.prep_time_minutes} min
                  </span>
                )}
                {recipe.cook_time_minutes && (
                  <span className="flex items-center gap-1">
                    🍳 Cook {recipe.cook_time_minutes} min
                  </span>
                )}
              </div>
            </div>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center
                       justify-center transition-colors">
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Modal body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">

          {recipe.parse_error ? (
            <p className="text-xs text-gray-600 whitespace-pre-wrap">{recipe.raw}</p>
          ) : (
            <>
              {/* Ingredients */}
              {recipe.ingredients && recipe.ingredients.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">
                    🛒 Ingredients
                  </h4>
                  <div className="space-y-2">
                    {recipe.ingredients.map((ing, i) => (
                      <div key={i}
                        className="flex items-center justify-between bg-gray-50
                                   rounded-xl px-3 py-2 border border-gray-100">
                        <span className="text-xs text-gray-700 font-medium">{ing.item}</span>
                        <span className="text-xs text-gray-400 font-semibold">
                          {ing.amount} {ing.unit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Steps */}
              {recipe.steps && recipe.steps.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">
                    👨‍🍳 Instructions
                  </h4>
                  <div className="space-y-3">
                    {recipe.steps.map((step, i) => (
                      <div key={i} className="flex gap-3">
                        <div className="w-6 h-6 rounded-full bg-blue-600 text-white
                                        flex items-center justify-center flex-shrink-0
                                        text-xs font-bold mt-0.5">
                          {i + 1}
                        </div>
                        <p className="text-xs text-gray-700 leading-relaxed pt-0.5">
                          {step.replace(/^Step \d+:\s*/i, "")}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Health tip */}
              {recipe.health_tip && (
                <div className="bg-green-50 border border-green-100 rounded-xl px-4 py-3">
                  <p className="text-xs text-green-700">
                    💚 <strong>Health tip:</strong> {recipe.health_tip}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Single Meal Card ──────────────────────────────────────────────────────────

function MealCard({ slot, meal, onSwap, onRecipe }: {
  slot: string;
  meal: MealSlot;
  onSwap:   (slot: string, currentName: string) => Promise<MealSlot | null>;
  onRecipe: (mealName: string) => Promise<Recipe | null>;
}) {
  const [currentMeal, setCurrentMeal]   = useState<MealSlot>(meal);
  const [swapping, setSwapping]         = useState(false);
  const [swapped, setSwapped]           = useState(false);
  const [recipeLoading, setRecipeLoading] = useState(false);
  const [recipe, setRecipe]             = useState<Recipe | null>(null);
  const [showRecipe, setShowRecipe]     = useState(false);

  const handleSwap = async () => {
    setSwapping(true);
    const newMeal = await onSwap(slot, currentMeal.name);
    if (newMeal && !newMeal.parse_error) {
      setCurrentMeal(newMeal);
      setRecipe(null); // clear old recipe when meal changes
      setSwapped(true);
      setTimeout(() => setSwapped(false), 3000);
    }
    setSwapping(false);
  };

  const handleRecipe = async () => {
    if (recipe) { setShowRecipe(true); return; } // already fetched
    setRecipeLoading(true);
    const r = await onRecipe(currentMeal.name);
    setRecipeLoading(false);
    if (r) {
      setRecipe(r);
      setShowRecipe(true);
    }
  };

  return (
    <>
      <div className={`bg-white rounded-2xl border shadow-sm overflow-hidden transition-all duration-300
        ${swapped ? "border-blue-300 ring-2 ring-blue-100" : "border-gray-100"}`}>

        {/* Header */}
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">{MEAL_ICONS[slot] || "🍽️"}</span>
            <div>
              <p className="text-[10px] text-gray-400 uppercase tracking-widest font-semibold">
                {slot}
              </p>
              <p className="text-sm font-bold text-gray-800 leading-tight">
                {currentMeal.name}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {/* Recipe button */}
            <button onClick={handleRecipe} disabled={recipeLoading}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5
                         rounded-full border border-gray-200 text-gray-500 bg-white
                         hover:border-green-300 hover:text-green-600 hover:bg-green-50
                         disabled:opacity-50 transition-all">
              <BookOpen className={`w-3 h-3 ${recipeLoading ? "animate-pulse" : ""}`} />
              {recipeLoading ? "Loading…" : "📖 Recipe"}
            </button>

            {/* Swap button */}
            <button onClick={handleSwap} disabled={swapping}
              className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5
                rounded-full border transition-all
                ${swapping
                  ? "border-blue-200 text-blue-400 bg-blue-50 cursor-not-allowed"
                  : swapped
                  ? "border-green-200 text-green-600 bg-green-50"
                  : "border-gray-200 text-gray-500 bg-white hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50"
                }`}>
              <RefreshCw className={`w-3 h-3 ${swapping ? "animate-spin" : ""}`} />
              {swapping ? "Swapping…" : swapped ? "✓ Swapped!" : "🔄 Swap"}
            </button>
          </div>
        </div>

        {/* Description */}
        <p className="text-xs text-gray-500 leading-relaxed px-4 pb-3">
          {currentMeal.description}
        </p>

        {/* Macros */}
        {currentMeal.macros && (
          <div className="grid grid-cols-4 gap-2 px-4 pb-3">
            {[
              { label: "Carbs",   value: currentMeal.macros.carbs_g,       unit: "g"  },
              { label: "Protein", value: currentMeal.macros.protein_g,     unit: "g"  },
              { label: "Fat",     value: currentMeal.macros.fat_g,         unit: "g"  },
              { label: "kcal",    value: currentMeal.macros.calories_kcal, unit: ""   },
            ].map(({ label, value, unit }) => (
              <div key={label}
                className="flex flex-col items-center bg-gray-50 rounded-xl px-2 py-2
                           border border-gray-100">
                <span className="text-sm font-bold text-gray-700">{value ?? "?"}{unit}</span>
                <span className="text-[10px] text-gray-400">{label}</span>
              </div>
            ))}
          </div>
        )}

        {/* Prep tip */}
        {currentMeal.prep_tip && (
          <div className="mx-4 mb-4 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2">
            <p className="text-xs text-amber-700">💡 {currentMeal.prep_tip}</p>
          </div>
        )}
      </div>

      {/* Recipe Modal */}
      {showRecipe && recipe && (
        <RecipeModal
          recipe={recipe}
          mealName={currentMeal.name}
          onClose={() => setShowRecipe(false)}
        />
      )}
    </>
  );
}

// ── Meal Plan Card (main export) ──────────────────────────────────────────────

export default function MealPlanCard({ plan, userId, onSwap, onRecipe }: Props) {
  if (!plan) return null;

  if (plan.parse_error || !plan.meals) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <h3 className="text-sm font-bold text-gray-700 mb-3">🥗 Your Meal Plan</h3>
        <p className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed">{plan.raw}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {plan.goal && (
        <div className="bg-blue-50 border border-blue-100 rounded-2xl px-4 py-3">
          <p className="text-xs text-blue-700">
            🎯 <strong>Today&apos;s Goal:</strong> {plan.goal}
          </p>
        </div>
      )}

      {Object.entries(plan.meals).map(([slot, meal]) => {
        if (!meal) return null;
        return (
          <MealCard
            key={slot}
            slot={slot}
            meal={meal}
            onSwap={onSwap}
            onRecipe={onRecipe}
          />
        );
      })}

      {plan.clinical_notes && (
        <div className="bg-red-50 border border-red-100 rounded-2xl px-4 py-3">
          <p className="text-xs text-red-700">
            📋 <strong>Clinical notes:</strong> {plan.clinical_notes}
          </p>
        </div>
      )}
    </div>
  );
}