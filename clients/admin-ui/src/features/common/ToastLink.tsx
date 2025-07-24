import { AntButton as Button } from "fidesui";
import { ReactNode } from "react";

import styles from "~/features/ToastLink.module.scss";

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
    size="small"
    className={styles.toastLink}
  >
    {children}
  </Button>
);

export default ToastLink;
