import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { SentimentBadge } from './SentimentBadge';

describe('SentimentBadge', () => {
  it('labels bullish sentiment above threshold', () => {
    render(<SentimentBadge avgSentiment={0.3} />);
    expect(screen.getByText('Bullish')).toBeInTheDocument();
  });
});
