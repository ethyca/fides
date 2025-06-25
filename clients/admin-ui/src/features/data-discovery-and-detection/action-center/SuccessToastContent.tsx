import ToastLink from "~/features/common/ToastLink";

export const SuccessToastContent = (
  message: string,
  onViewClick?: () => void,
) => (
  <>
    {message} {onViewClick && <ToastLink onClick={onViewClick}>View</ToastLink>}
  </>
);
