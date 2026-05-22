/**
 * pages/index.tsx
 * ────────────────
 * Main application — Login + Dashboard with custom chat sidebar.
 * No CopilotKit dependency — uses direct /agent calls.
 */

"use client";

import { useState, useRef, useEffect } from "react";
import CGMChart from "@/components/CGMChart";
import MoodChart from "@/components/MoodChart";
import FoodLogForm from "@/components/FoodLogForm";
import MealPlanCard from "@/components/MealPlanCard";
import { useAgent } from "@/hooks/useAgent";
import {
  Activity, Heart, Utensils, ClipboardList,
  LogIn, RefreshCw, AlertCircle, Send, Bot, User,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface Message {
  role: "user" | "assistant";
  text: string;
  time: string;
}

function now() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// ── Chat Sidebar ──────────────────────────────────────────────────────────────

function ChatSidebar({
  messages,
  onSend,
  loading,
}: {
  messages: Message[];
  onSend: (text: string) => void;
  loading: boolean;
}) {
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <div className="w-80 flex flex-col bg-white border-l border-gray-200 h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-brand-600">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-white" />
          <div>
            <p className="text-sm font-semibold text-white">HealthCare AI Assistant</p>
            <p className="text-xs text-brand-100">Ask me anything</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 chat-scrollbar">
        {messages.length === 0 && (
          <div className="text-center text-xs text-gray-400 mt-8 px-4">
            <Bot className="w-8 h-8 mx-auto mb-2 opacity-30" />
            Ask me to log your mood, CGM reading, food, generate a meal plan,
            or any general health question!
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-1
              ${m.role === "user" ? "bg-brand-600" : "bg-gray-200"}`}>
              {m.role === "user"
                ? <User className="w-3 h-3 text-white" />
                : <Bot className="w-3 h-3 text-gray-600" />}
            </div>
            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs
              ${m.role === "user"
                ? "bg-brand-600 text-white rounded-tr-none"
                : "bg-gray-100 text-gray-800 rounded-tl-none"}`}>
              <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
              <p className={`text-[10px] mt-1 ${m.role === "user" ? "text-brand-200" : "text-gray-400"}`}>
                {m.time}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
              <Bot className="w-3 h-3 text-gray-600" />
            </div>
            <div className="bg-gray-100 rounded-xl rounded-tl-none px-3 py-2">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-xs
                       focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Type a message…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50
                       text-white rounded-lg p-2 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[10px] text-gray-400 mt-1 text-center">
          Try: "log mood happy" · "cgm 145" · "what is insulin?"
        </p>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function Home() {
  const { callAgent, fetchCGMHistory, fetchMoodHistory, loading, error } = useAgent();

  const [userId, setUserId]         = useState("");
  const [user, setUser]             = useState<any>(null);
  const [loginError, setLoginError] = useState("");

  const [cgmInput, setCgmInput]   = useState("");
  const [cgmHistory, setCgmHistory]   = useState<any[]>([]);
  const [moodHistory, setMoodHistory] = useState<any[]>([]);
  const [mealPlan, setMealPlan]       = useState<any>(null);
  const [activeTab, setActiveTab]     = useState<"dashboard" | "meals" | "food">("dashboard");

  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [chatLoading, setChatLoading]   = useState(false);

  // ── helpers ────────────────────────────────────────────────────────────────

  const addMsg = (role: "user" | "assistant", text: string) =>
    setChatMessages((prev) => [...prev, { role, text, time: now() }]);

  const refreshCharts = async (uid: number) => {
    const [cgm, mood] = await Promise.all([
      fetchCGMHistory(uid),
      fetchMoodHistory(uid),
    ]);
    setCgmHistory(cgm || []);
    setMoodHistory(mood || []);
  };

  // ── login ──────────────────────────────────────────────────────────────────

  const handleLogin = async () => {
    const id = parseInt(userId, 10);
    if (isNaN(id)) { setLoginError("Please enter a numeric User ID."); return; }
    const res = await callAgent("greet", { user_id: id });
    if (!res) { setLoginError("Cannot reach backend. Is it running on port 8000?"); return; }
    if (!res.result?.valid) { setLoginError(res.result?.message || "Invalid ID."); return; }
    setUser(res.result.user);
    setLoginError("");
    addMsg("assistant", res.result.message);
    await refreshCharts(id);
  };

  // ── dashboard actions ──────────────────────────────────────────────────────

  const handleMoodSubmit = async (mood: string) => {
    const res = await callAgent("mood", { user_id: user.user_id, mood });
    if (res?.result?.message) addMsg("assistant", res.result.message);
    await refreshCharts(user.user_id);
  };

  const handleCGMSubmit = async () => {
    if (!cgmInput) return;
    const res = await callAgent("cgm", { user_id: user.user_id, reading: parseFloat(cgmInput) });
    if (res?.result?.alert_message) addMsg("assistant", res.result.alert_message);
    setCgmInput("");
    await refreshCharts(user.user_id);
  };

  const handleFoodLog = async (description: string, timestamp: string) => {
    const res = await callAgent("food", { user_id: user.user_id, description, timestamp });
    if (res?.result?.message) addMsg("assistant", res.result.message);
  };

  const handleMealPlan = async () => {
    addMsg("assistant", "Generating your personalised meal plan… ⏳");
    const res = await callAgent("meal_plan", { user_id: user.user_id });
    if (res?.result) {
      setMealPlan(res.result.plan);
      addMsg("assistant", res.result.message);
      setActiveTab("meals");
    }
  };

  // ── chat sidebar handler ───────────────────────────────────────────────────

  const handleChatSend = async (text: string) => {
    addMsg("user", text);
    setChatLoading(true);

    try {
      const lower = text.toLowerCase();

      // Mood detection
      const moods = ["happy","sad","excited","tired","anxious","calm","angry","neutral","content"];
      const detectedMood = moods.find((m) => lower.includes(m));

      if (lower.includes("meal plan") || lower.includes("meal") && lower.includes("plan")) {
        const res = await callAgent("meal_plan", { user_id: user.user_id });
        if (res?.result) {
          setMealPlan(res.result.plan);
          addMsg("assistant", res.result.message);
          setActiveTab("meals");
        }
      } else if (lower.startsWith("cgm") || lower.includes("glucose") || lower.includes("reading")) {
        const match = text.match(/\d+(\.\d+)?/);
        if (match) {
          const res = await callAgent("cgm", { user_id: user.user_id, reading: parseFloat(match[0]) });
          if (res?.result?.alert_message) addMsg("assistant", res.result.alert_message);
          await refreshCharts(user.user_id);
        } else {
          addMsg("assistant", "Please include your glucose value, e.g. 'cgm 145'");
        }
      } else if ((lower.includes("mood") || lower.includes("feeling") || lower.includes("feel")) && detectedMood) {
        const res = await callAgent("mood", { user_id: user.user_id, mood: detectedMood });
        if (res?.result?.message) addMsg("assistant", res.result.message);
        await refreshCharts(user.user_id);
      } else if (detectedMood && lower.split(" ").length <= 3) {
        const res = await callAgent("mood", { user_id: user.user_id, mood: detectedMood });
        if (res?.result?.message) addMsg("assistant", res.result.message);
        await refreshCharts(user.user_id);
      } else if (lower.includes("ate") || lower.includes("eat") || lower.includes("food") || lower.includes("had") || lower.includes("lunch") || lower.includes("dinner") || lower.includes("breakfast")) {
        const res = await callAgent("food", { user_id: user.user_id, description: text, timestamp: new Date().toISOString() });
        if (res?.result?.message) addMsg("assistant", res.result.message);
      } else {
        // General Q&A — interrupt agent
        const res = await callAgent("interrupt", { query: text, current_flow: activeTab });
        if (res?.result?.answer) addMsg("assistant", res.result.answer);
      }
    } finally {
      setChatLoading(false);
    }
  };

  // ── Login screen ───────────────────────────────────────────────────────────

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-brand-50 to-white
                      flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">HealthCare AI</h1>
              <p className="text-xs text-gray-400">Personalised Multi-Agent Demo</p>
            </div>
          </div>

          <p className="text-sm text-gray-600 mb-5">
            Enter your User ID (1–100) to begin your personalised health session.
          </p>

          <input
            type="number" min={1} max={100}
            placeholder="Enter User ID (e.g. 7)"
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm
                       focus:outline-none focus:ring-2 focus:ring-brand-500 mb-3"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
          />

          {loginError && (
            <div className="flex items-center gap-2 text-red-600 text-xs mb-3">
              <AlertCircle className="w-4 h-4" />{loginError}
            </div>
          )}

          <button
            onClick={handleLogin} disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50
                       text-white rounded-lg py-3 text-sm font-medium
                       flex items-center justify-center gap-2 transition-colors"
          >
            <LogIn className="w-4 h-4" />
            {loading ? "Verifying…" : "Start Session"}
          </button>
        </div>
      </div>
    );
  }

  // ── Dashboard ──────────────────────────────────────────────────────────────

  const TABS = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "meals",     label: "Meal Plan",  icon: ClipboardList },
    { id: "food",      label: "Food Log",   icon: Utensils },
  ] as const;

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">

      {/* ── Main panel ── */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">

        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <Heart className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">
                Hello, {user.first_name} {user.last_name}!
              </p>
              <p className="text-xs text-gray-400">{user.city} · ID #{user.user_id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-brand-50 text-brand-700 rounded-full px-2 py-1">
              {user.dietary_preference}
            </span>
            <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-1 hidden sm:block">
              {user.medical_conditions}
            </span>
            <button
              onClick={() => refreshCharts(user.user_id)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </header>

        {/* Tabs */}
        <div className="bg-white border-b border-gray-200 px-6 flex gap-4">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 py-3 text-sm border-b-2 transition-colors
                ${activeTab === id
                  ? "border-brand-600 text-brand-700 font-medium"
                  : "border-transparent text-gray-500 hover:text-gray-700"}`}
            >
              <Icon className="w-4 h-4" />{label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">

          {activeTab === "dashboard" && (
            <>
              <div className="grid grid-cols-2 gap-4">
                {/* CGM */}
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-brand-600" /> Log CGM Reading
                  </h3>
                  <div className="flex gap-2">
                    <input
                      type="number" placeholder="mg/dL"
                      className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm
                                 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      value={cgmInput}
                      onChange={(e) => setCgmInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleCGMSubmit()}
                    />
                    <button
                      onClick={handleCGMSubmit} disabled={loading || !cgmInput}
                      className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50
                                 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                    >Log</button>
                  </div>
                </div>

                {/* Mood */}
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Heart className="w-4 h-4 text-rose-500" /> Log Mood
                  </h3>
                  <div className="flex gap-2 flex-wrap">
                    {["happy","sad","excited","tired","anxious","calm"].map((m) => (
                      <button key={m} onClick={() => handleMoodSubmit(m)}
                        className="text-xs px-2 py-1 rounded-full border border-gray-300
                                   hover:bg-brand-50 hover:border-brand-300 transition-colors capitalize">
                        {m}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <CGMChart data={cgmHistory} />
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <MoodChart data={moodHistory} />
              </div>

              <button
                onClick={handleMealPlan} disabled={loading}
                className="w-full bg-gradient-to-r from-brand-600 to-brand-500
                           hover:from-brand-700 hover:to-brand-600 disabled:opacity-50
                           text-white rounded-xl py-3 text-sm font-semibold
                           flex items-center justify-center gap-2 transition-all shadow-sm"
              >
                <ClipboardList className="w-4 h-4" />
                {loading ? "Generating…" : "✨ Generate Today's Meal Plan"}
              </button>
            </>
          )}

          {activeTab === "meals" && (
            mealPlan ? <MealPlanCard plan={mealPlan} /> : (
              <div className="text-center py-12 text-gray-400">
                <ClipboardList className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No meal plan yet.</p>
                <button onClick={handleMealPlan} disabled={loading}
                  className="mt-4 bg-brand-600 text-white rounded-lg px-5 py-2
                             text-sm font-medium hover:bg-brand-700 transition-colors">
                  Generate Meal Plan
                </button>
              </div>
            )
          )}

          {activeTab === "food" && (
            <FoodLogForm onSubmit={handleFoodLog} loading={loading} />
          )}

          {error && (
            <div className="flex items-center gap-2 text-red-600 text-xs bg-red-50
                             border border-red-100 rounded-lg px-3 py-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />{error}
            </div>
          )}
        </div>
      </div>

      {/* ── Chat Sidebar ── */}
      <ChatSidebar
        messages={chatMessages}
        onSend={handleChatSend}
        loading={chatLoading}
      />
    </div>
  );
}