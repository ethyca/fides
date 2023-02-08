import { Button, forwardRef } from "@fidesui/react";

/**
 * Provides the default styling props for buttons used by Privacy Request actions.
 */
export const StyledButton: typeof Button = forwardRef((props, ref) => (
  <Button
    ref={ref}
    size="xs"
    bg="white"
    _loading={{
      opacity: 1,
      div: { opacity: 0.4 },
    }}
    _hover={{
      bg: "gray.100",
    }}
    {...props}
  />
));

export default StyledButton;
