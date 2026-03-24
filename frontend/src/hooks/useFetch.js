import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../context/AppContext';

const cache = new Map();
const CACHE_TTL = 30_000;

export function useFetch(path, options = {}) {
  const { enabled = true, ttl = CACHE_TTL } = options;
  const [data, setData] = useState(cache.get(path)?.data || null);
  const [loading, setLoading] = useState(!cache.has(path));
  const [error, setError] = useState(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchApi(path);
      setData(result);
      cache.set(path, { data: result, ts: Date.now() });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    if (!enabled) return;

    const cached = cache.get(path);
    if (cached && Date.now() - cached.ts < ttl) {
      setData(cached.data);
      setLoading(false);
      return;
    }

    refetch();
  }, [path, enabled, refetch]);

  return { data, loading, error, refetch };
}

export function invalidateCache(prefix) {
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) cache.delete(key);
  }
}
