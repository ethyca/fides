// __tests__/RequestModal.test.tsx
import {
  fireEvent,
  render,
  screen,
  waitFor,
  waitForElementToBeRemoved,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { rest } from "msw";
import { setupServer } from "msw/node";
import { act } from "react-dom/test-utils";

import {
  PrivacyRequestModal,
  RequestModalProps,
} from "~/components/modals/privacy-request-modal/PrivacyRequestModal";
import { ModalViews } from "~/components/modals/types";
import { hostUrl } from "~/constants";
import IndexPage from "../pages/index";

import mockConfig from "../config/__mocks__/config.json";

jest.mock("../config/config.json");

const server = setupServer(
  rest.get(`${hostUrl}/id-verification/config`, (req, res, ctx) =>
    res(
      ctx.json({
        identity_verification_required: false,
        valid_email_config_exists: false,
      })
    )
  )
);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const defaultModalProperties: RequestModalProps = {
  isOpen: true,
  onClose: () => {},
  openAction: mockConfig.actions[0].policy_key,
  currentView: ModalViews.PrivacyRequest,
  setCurrentView: () => {},
  privacyRequestId: "",
  setPrivacyRequestId: () => {},
  isVerificationRequired: false,
  successHandler: () => {},
};

describe("RequestModal", () => {
  it("renders a modal when isOpen is true", () => {
    render(<PrivacyRequestModal {...defaultModalProperties} />);

    const modal = screen.getByRole("dialog");
    expect(modal).toBeInTheDocument();
  });

  it("renders the appropriate inputs", () => {
    let { unmount } = render(
      <PrivacyRequestModal {...defaultModalProperties} />
    );

    expect(screen.getByPlaceholderText("Michael Brown")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("test-email@example.com")
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("+1 000 000 0000")).toBeInTheDocument();

    unmount();

    ({ unmount } = render(
      <PrivacyRequestModal
        {...defaultModalProperties}
        openAction={mockConfig.actions[1].policy_key}
      />
    ));

    expect(screen.getByPlaceholderText("Michael Brown")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("test-email@example.com")
    ).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("+1 000 000 0000")).toBeNull();

    unmount();

    ({ unmount } = render(
      <PrivacyRequestModal
        {...defaultModalProperties}
        openAction={mockConfig.actions[2].policy_key}
      />
    ));

    expect(screen.queryByPlaceholderText("Michael Brown")).toBeNull();
    expect(screen.queryByPlaceholderText("test-email@example.com")).toBeNull();
    expect(screen.getByPlaceholderText("+1 000 000 0000")).toBeInTheDocument();

    unmount();
  });

  it("renders the button as disabled before inputs are filled", () => {
    render(<PrivacyRequestModal {...defaultModalProperties} />);
    const submitButton = screen.getByText("Continue");
    expect(submitButton).toBeDisabled();
  });

  it("renders the button as enabled after inputs are filled correctly", async () => {
    render(<PrivacyRequestModal {...defaultModalProperties} />);
    act(() => {
      fireEvent.change(screen.getByPlaceholderText("Michael Brown"), {
        target: { value: "Ethyca" },
      });

      fireEvent.change(screen.getByPlaceholderText("test-email@example.com"), {
        target: { value: "testing@ethyca.com" },
      });

      fireEvent.change(screen.getByPlaceholderText("000 000 0000"), {
        target: { value: "0000000000" },
      });
    });

    const submitButton = await screen.getByText("Continue");
    await waitFor(() => expect(submitButton).not.toBeDisabled());
  });

  it("handles form submission success with an appropriate alert", async () => {
    render(<IndexPage />);
    server.use(
      rest.post(`${hostUrl}/privacy-request`, (req, res, ctx) =>
        res(
          ctx.json({
            succeeded: [{}],
            failed: [],
          })
        )
      )
    );

    act(() => {
      fireEvent.click(screen.getAllByRole("button")[0]);
    });

    act(() => {
      fireEvent.change(screen.getByPlaceholderText("Michael Brown"), {
        target: { value: "Ethyca" },
      });

      fireEvent.change(screen.getByPlaceholderText("test-email@example.com"), {
        target: { value: "testing@ethyca.com" },
      });

      fireEvent.change(screen.getByPlaceholderText("000 000 0000"), {
        target: { value: "0000000000" },
      });
    });

    act(() => {
      userEvent.click(screen.getByText("Continue"));
    });

    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"));
  });

  it("handles form submission failure with an appropriate alert", async () => {
    render(<IndexPage />);
    server.use(
      rest.post(`${hostUrl}/privacy-request`, (req, res, ctx) =>
        res(
          ctx.json({
            succeeded: [],
            failed: [{}],
          })
        )
      )
    );

    act(() => {
      fireEvent.click(screen.getAllByRole("button")[0]);
    });

    act(() => {
      fireEvent.change(screen.getByPlaceholderText("Michael Brown"), {
        target: { value: "Ethyca" },
      });

      fireEvent.change(screen.getByPlaceholderText("test-email@example.com"), {
        target: { value: "testing@ethyca.com" },
      });

      fireEvent.change(screen.getByPlaceholderText("000 000 0000"), {
        target: { value: "0000000000" },
      });
    });

    act(() => {
      userEvent.click(screen.getByText("Continue"));
    });
  });
});
