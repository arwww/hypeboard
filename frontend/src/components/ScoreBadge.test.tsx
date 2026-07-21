import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ScoreBadge } from './ScoreBadge';

describe('ScoreBadge', () => {
  it('renders a score and its coverage without presenting a percentage of retail ownership', () => {
    render(<ScoreBadge value={85.2} label="Hype Score" size="large" showCoverage={0.65} />);
    expect(screen.getByLabelText('Hype Score: 85')).toBeInTheDocument();
    expect(screen.getByText('65% coverage')).toBeInTheDocument();
    expect(screen.queryByText(/retail ownership/i)).not.toBeInTheDocument();
  });

  it('renders missing scores explicitly', () => {
    render(<ScoreBadge value={null} label="Trading" />);
    expect(screen.getByLabelText('Trading: —')).toBeInTheDocument();
  });
});
