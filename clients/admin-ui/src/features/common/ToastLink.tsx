import { AntButton as Button } from "fidesui";
import { ReactNode } from "react";

// It's difficult to pass a NextLink directly into a toast, so we can use a styled button instead,
// where the onClick can use the next router
// https://github.com/chakra-ui/chakra-ui/issues/3690
const ToastLink = ({
  onClick,
  children,
}: {
  onClick: () => void;
  children: ReactNode;
}) => (
  <Button
    onClick={onClick}
    type="link"
    role="link"
    size="large"
    className="m-0 p-0 font-medium text-gray-700 underline"
  >
    {children}
  </Button>
);

export default ToastLink;
