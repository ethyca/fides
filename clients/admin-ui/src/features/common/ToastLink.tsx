import { Button } from "@fidesui/react";
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
    as="a"
    onClick={onClick}
    variant="link"
    textDecor="underline"
    textColor="gray.700"
    fontWeight="medium"
    // allow lines to wrap
    display="initial"
    cursor="pointer"
    whiteSpace="inherit"
  >
    {children}
  </Button>
);

export default ToastLink;
