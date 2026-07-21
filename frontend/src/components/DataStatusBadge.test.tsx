import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DataStatusBadge } from './DataStatusBadge';

describe('DataStatusBadge', () => {
  it.each([
    ['fresh', 'Fresh'],
    ['cached', 'Cached'],
    ['stale', 'Stale'],
    ['partial', 'Partial'],
    ['unavailable', 'Unavailable'],
  ] as const)('renders %s data as %s', (status, label) => {
    render(<DataStatusBadge status={status} />);
    expect(screen.getByText(label)).toHaveClass(`status-${status}`);
  });
});
