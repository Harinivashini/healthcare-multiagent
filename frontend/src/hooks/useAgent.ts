/**
 * hooks/useAgent.ts
 * ──────────────────
 * React hook that wraps all backend /agent calls.
 */

import { useState } from "react";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Intent =
  | "greet"
  | "mood"
  | "cgm"
  | "food"
  | "meal_plan"
  | "interrupt";

interface AgentResponse {
  intent: string;
  result: any;
  error?: string;
}

export function useAgent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const callAgent = async (
    intent: Intent,
    payload: Record<string, any>
  ): Promise<AgentResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.post<AgentResponse>(`${API_URL}/agent`, {
        intent,
        payload,
      });
      return data;
    } catch (err: any) {
      const msg =
        err.response?.data?.detail || err.message || "Unknown error";
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const fetchUserProfile = async (userId: number) => {
    const { data } = await axios.get(`${API_URL}/users/${userId}`);
    return data;
  };

  const fetchCGMHistory = async (userId: number) => {
    const { data } = await axios.get(`${API_URL}/users/${userId}/cgm`);
    return data.cgm_history;
  };

  const fetchMoodHistory = async (userId: number) => {
    const { data } = await axios.get(`${API_URL}/users/${userId}/mood`);
    return data.mood_history;
  };

  const fetchFoodHistory = async (userId: number) => {
    const { data } = await axios.get(`${API_URL}/users/${userId}/food`);
    return data.food_history;
  };

  const fetchAlerts = async (userId: number) => {
    const { data } = await axios.get(`${API_URL}/users/${userId}/alerts`);
    return data.alerts;
  };

  return {
    callAgent,
    fetchUserProfile,
    fetchCGMHistory,
    fetchMoodHistory,
    fetchFoodHistory,
    fetchAlerts,
    loading,
    error,
  };
}