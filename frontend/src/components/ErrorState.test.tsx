import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ErrorState } from './ErrorState';

describe('ErrorState', () => {
  it('shows a useful failure state when JSON cannot be loaded', () => {
    render(<ErrorState message="Data request failed (404)" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Dashboard data could not be loaded');
    expect(screen.getByRole('alert')).toHaveTextContent('Data request failed (404)');
  });
});
