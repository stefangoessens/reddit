'use client';

import { useEffect, useState } from 'react';

import type { AlertEvent } from '@/lib/types';

export function useAlerts(maxItems = 10) {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8080';
    const source = new EventSource(`${apiBase}/v1/alerts/live`);
    source.onmessage = (event) => {
      const data = JSON.parse(event.data) as AlertEvent;
      setAlerts((prev) => [data, ...prev].slice(0, maxItems));
    };
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  }, [maxItems]);

  return alerts;
}
