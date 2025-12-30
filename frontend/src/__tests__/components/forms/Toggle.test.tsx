/**
 * Toggle Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Toggle from '../../../components/forms/Toggle';

describe('Toggle Component', () => {
  it('should render toggle with label', () => {
    render(
      <Toggle
        id="test-toggle"
        label="Test Toggle"
        checked={false}
        onChange={vi.fn()}
      />
    );

    expect(screen.getByText('Test Toggle')).toBeInTheDocument();
  });

  it('should render description when provided', () => {
    render(
      <Toggle
        id="test-toggle"
        label="Test Toggle"
        checked={false}
        onChange={vi.fn()}
        description="This is a test description"
      />
    );

    expect(screen.getByText('This is a test description')).toBeInTheDocument();
  });

  it('should call onChange when clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <Toggle
        id="test-toggle"
        label="Test Toggle"
        checked={false}
        onChange={onChange}
      />
    );

    const toggle = screen.getByRole('switch');
    await user.click(toggle);

    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('should reflect checked state', () => {
    render(
      <Toggle
        id="test-toggle"
        label="Test Toggle"
        checked={true}
        onChange={vi.fn()}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'true');
  });

  it('should reflect unchecked state', () => {
    render(
      <Toggle
        id="test-toggle"
        label="Test Toggle"
        checked={false}
        onChange={vi.fn()}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });

  it('should be disabled when disabled prop is true', () => {
    render(
      <Toggle
        id="test-toggle"
        label="Test Toggle"
        checked={false}
        onChange={vi.fn()}
        disabled={true}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeDisabled();
  });

  it('should not call onChange when disabled', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <Toggle
        id="test-toggle"
        label="Test Toggle"
        checked={false}
        onChange={onChange}
        disabled={true}
      />
    );

    const toggle = screen.getByRole('switch');
    await user.click(toggle);

    expect(onChange).not.toHaveBeenCalled();
  });
});

