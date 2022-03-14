// __tests__/RequestModal.test.tsx
import {
  fireEvent,
  render,
  screen,
  waitFor,
  waitForElementToBeRemoved,
} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react-dom/test-utils';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

import { RequestModal } from '../components/RequestModal';
import IndexPage from '../pages/index';

import mockConfig from '../config/__mocks__/config.json';

jest.mock('../config/config.json');

const server = setupServer();
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const defaultModalProperties = {
  isOpen: true,
  onClose: () => {},
  openAction: mockConfig.actions[0].policy_key,
  setAlert: () => {},
};

describe('RequestModal', () => {
  it('renders a modal when isOpen is true', () => {
    render(<RequestModal {...defaultModalProperties} />);

    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();
  });

  it('renders the appropriate inputs', () => {
    let { unmount } = render(<RequestModal {...defaultModalProperties} />);

    expect(screen.getByPlaceholderText('Name*')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email*')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Phone')).toBeInTheDocument();

    unmount();

    ({ unmount } = render(
      <RequestModal
        {...defaultModalProperties}
        openAction={mockConfig.actions[1].policy_key}
      />
    ));

    expect(screen.getByPlaceholderText('Name')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email*')).toBeInTheDocument();
    expect(screen.queryByPlaceholderText('Phone')).toBeNull();

    unmount();

    ({ unmount } = render(
      <RequestModal
        {...defaultModalProperties}
        openAction={mockConfig.actions[2].policy_key}
      />
    ));

    expect(screen.queryByPlaceholderText('Name')).toBeNull();
    expect(screen.queryByPlaceholderText('Email')).toBeNull();
    expect(screen.getByPlaceholderText('Phone')).toBeInTheDocument();

    unmount();
  });

  it('renders the button as disabled before inputs are filled', () => {
    render(<RequestModal {...defaultModalProperties} />);
    const submitButton = screen.getByText('Continue');
    expect(submitButton).toBeDisabled();
  });

  it('renders the button as enabled after inputs are filled correctly', async () => {
    render(<RequestModal {...defaultModalProperties} />);
    act(() => {
      fireEvent.change(screen.getByPlaceholderText('Name*'), {
        target: { value: 'Ethyca' },
      });

      fireEvent.change(screen.getByPlaceholderText('Email*'), {
        target: { value: 'testing@ethyca.com' },
      });

      fireEvent.change(screen.getByPlaceholderText('Phone'), {
        target: { value: '0000000000' },
      });
    });

    const submitButton = await screen.getByText('Continue');
    await waitFor(() => expect(submitButton).not.toBeDisabled());
  });

  it('handles form submission success with an appropriate alert', async () => {
    render(<IndexPage />);
    server.use(
      rest.post(
        `${mockConfig.fidesops_host_production}/privacy-request`,
        (req, res, ctx) =>
          res(
            ctx.json({
              succeeded: [{}],
              failed: [],
            })
          )
      )
    );

    act(() => {
      fireEvent.click(screen.getAllByRole('button')[0]);
    });

    act(() => {
      fireEvent.change(screen.getByPlaceholderText('Name*'), {
        target: { value: 'Ethyca' },
      });

      fireEvent.change(screen.getByPlaceholderText('Email*'), {
        target: { value: 'testing@ethyca.com' },
      });

      fireEvent.change(screen.getByPlaceholderText('Phone'), {
        target: { value: '0000000000' },
      });
    });

    act(() => {
      userEvent.click(screen.getByText('Continue'));
    });

    await waitForElementToBeRemoved(() => screen.queryByRole('dialog'));

    const notification = await screen.getByText(
      'Your request was successful, please await further instructions.'
    );
    expect(notification).toBeInTheDocument();
  });

  it('handles form submission failure with an appropriate alert', async () => {
    render(<IndexPage />);
    server.use(
      rest.post(
        `${mockConfig.fidesops_host_production}/privacy-request`,
        (req, res, ctx) =>
          res(
            ctx.json({
              succeeded: [],
              failed: [{}],
            })
          )
      )
    );

    act(() => {
      fireEvent.click(screen.getAllByRole('button')[0]);
    });

    act(() => {
      fireEvent.change(screen.getByPlaceholderText('Name*'), {
        target: { value: 'Ethyca' },
      });

      fireEvent.change(screen.getByPlaceholderText('Email*'), {
        target: { value: 'testing@ethyca.com' },
      });

      fireEvent.change(screen.getByPlaceholderText('Phone'), {
        target: { value: '0000000000' },
      });
    });

    act(() => {
      userEvent.click(screen.getByText('Continue'));
    });

    await waitForElementToBeRemoved(() => screen.queryByRole('dialog'));

    const notification = await screen.getByText(
      'Your request has failed. Please try again.'
    );
    expect(notification).toBeInTheDocument();
  });
});
