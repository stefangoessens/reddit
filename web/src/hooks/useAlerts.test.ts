import { beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';

import { useAlerts } from './useAlerts';

class MockEventSource {
  static instances: MockEventSource[] = [];
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(public url: string) {
    MockEventSource.instances.push(this);
  }

  emit(data: object) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  }

  close() {}
}

vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource);

describe('useAlerts', () => {
  beforeEach(() => {
    MockEventSource.instances = [];
  });

  it('streams alerts and caps list length', () => {
    const { result } = renderHook(() => useAlerts(2));
    const instance = MockEventSource.instances[0];

    act(() => {
      instance.emit({ ts: '2024-01-01T00:00:00Z', ticker: 'PLTR', tier: 'heads-up', hypeScore: 1.2, zscore: 3, uniqueAuthors: 4, threadsTouched: 2, avgSentiment: 0.2 });
      instance.emit({ ts: '2024-01-01T00:01:00Z', ticker: 'TSLA', tier: 'actionable', hypeScore: 2.5, zscore: 4, uniqueAuthors: 5, threadsTouched: 3, avgSentiment: 0.3 });
      instance.emit({ ts: '2024-01-01T00:02:00Z', ticker: 'GME', tier: 'heads-up', hypeScore: 1.0, zscore: 2, uniqueAuthors: 3, threadsTouched: 1, avgSentiment: -0.1 });
    });

    expect(result.current).toHaveLength(2);
    expect(result.current[0].ticker).toBe('GME');
  });
});
