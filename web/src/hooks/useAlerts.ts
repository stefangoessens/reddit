'use client';

import { useEffect, useState } from 'react';

import type { AlertEvent } from '@/lib/types';

export function useAlerts(maxItems = 10) {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);

  useEffect(() => {
    // Hardcoded for Railway deployment - environment variable not being picked up during build
    const apiBase = 'https://reddit-production-e3de.up.railway.app';
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
