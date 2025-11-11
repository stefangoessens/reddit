'use client';

import { useEffect, useState } from 'react';

import type { AlertEvent } from '@/lib/types';
import { API_BASE } from '@/lib/env';

export function useAlerts(maxItems = 10) {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);

  useEffect(() => {
    const source = new EventSource(`${API_BASE}/v1/alerts/live`);
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
