// __tests__/index.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Home from '../pages/index';

import mockConfig from '../config/__mocks__/config.json';

jest.mock('../config/config.json');

describe('Home', () => {
  it('renders a heading from config', () => {
    render(<Home />);

    const heading = screen.getByRole('heading', {
      name: mockConfig.title,
    });

    expect(heading).toBeInTheDocument();
  });

  it('renders a description from config', () => {
    render(<Home />);
    const heading = screen.getByText(mockConfig.description);
    expect(heading).toBeInTheDocument();
  });

  it('renders the correct number of action cards', () => {
    render(<Home />);
    mockConfig.actions.forEach((action) => {
      const cardHeading = screen.getByText(action.title);
      expect(cardHeading).toBeInTheDocument();

      const cardDescription = screen.getByText(action.description);
      expect(cardDescription).toBeInTheDocument();
    });
  });

  it('opens a modal when an action card is clicked', () => {
    render(<Home />);
    const card = screen.getAllByRole('button')[0];
    fireEvent.click(card);
    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();
  });

  it('renders the logo from the corrrect url', async () => {
    render(<Home />);
    await waitFor(() => {
      const logo = screen.getByAltText('Logo');
      expect(logo.src).toEqual(`http://localhost${mockConfig.logo_path}`);
    });
  })
});
