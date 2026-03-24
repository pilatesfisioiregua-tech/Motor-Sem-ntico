import { useEffect, useRef } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

export function useSSE(path, onMessage) {
  const cbRef = useRef(onMessage);
  cbRef.current = onMessage;

  useEffect(() => {
    const url = `${BASE}${path}`;
    let source = new EventSource(url);

    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        cbRef.current(data);
      } catch (e) {
        console.warn('SSE parse error:', e);
      }
    };

    source.onerror = () => {
      source.close();
      setTimeout(() => {
        source = new EventSource(url);
      }, 5000);
    };

    return () => source.close();
  }, [path]);
}
