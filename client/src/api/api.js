const BASE = import.meta.env.VITE_API_URL || "";

export async function fetchPrediction(input) {
  const res = await fetch(`${BASE}/api/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || "Prediction request failed.");
  }

  return data;
}
