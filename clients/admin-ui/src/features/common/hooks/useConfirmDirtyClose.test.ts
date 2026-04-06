import { act, renderHook } from "@testing-library/react";
import { useModal } from "fidesui";

import useConfirmDirtyClose from "./useConfirmDirtyClose";

jest.mock("fidesui", () => ({
  useModal: jest.fn(),
}));

describe("useConfirmDirtyClose", () => {
  const mockConfirm = jest.fn();
  const mockDestroy = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockConfirm.mockReturnValue({ destroy: mockDestroy });
    (useModal as jest.Mock).mockReturnValue({ confirm: mockConfirm });
  });

  it("calls onClose immediately when form is clean", () => {
    const onClose = jest.fn();
    const getIsDirty = jest.fn().mockReturnValue(false);

    const { result } = renderHook(() =>
      useConfirmDirtyClose(onClose, getIsDirty),
    );

    act(() => {
      result.current();
    });

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(mockConfirm).not.toHaveBeenCalled();
  });

  it("shows confirm dialog when form is dirty", () => {
    const onClose = jest.fn();
    const getIsDirty = jest.fn().mockReturnValue(true);

    const { result } = renderHook(() =>
      useConfirmDirtyClose(onClose, getIsDirty),
    );

    act(() => {
      result.current();
    });

    expect(onClose).not.toHaveBeenCalled();
    expect(mockConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when user confirms discard", () => {
    const onClose = jest.fn();
    const getIsDirty = jest.fn().mockReturnValue(true);

    const { result } = renderHook(() =>
      useConfirmDirtyClose(onClose, getIsDirty),
    );

    act(() => {
      result.current();
    });

    const { onOk } = mockConfirm.mock.calls[0][0];
    act(() => {
      onOk();
    });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("destroys orphaned confirm dialog on unmount", () => {
    const onClose = jest.fn();
    const getIsDirty = jest.fn().mockReturnValue(true);

    const { result, unmount } = renderHook(() =>
      useConfirmDirtyClose(onClose, getIsDirty),
    );

    act(() => {
      result.current();
    });

    expect(mockDestroy).not.toHaveBeenCalled();

    unmount();

    expect(mockDestroy).toHaveBeenCalledTimes(1);
  });
});
