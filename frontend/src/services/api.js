const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export const checkHealth = async () => {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json();
};