import { Button, ButtonProps } from "@fidesui/react";

type ButtonVariant = "primary" | "outline";

const AddProperty = ({
  buttonLabel,
  buttonVariant = "primary",
  onButtonClick,
}: {
  buttonLabel?: string;
  buttonVariant?: ButtonVariant;
  onButtonClick?: () => void;
}) => {
  const handleOpenButtonClicked = () => {
    if (onButtonClick) {
      onButtonClick();
    }
  };

  const openButtonStyles: ButtonProps =
    buttonVariant === "primary"
      ? {
          size: "sm",
          colorScheme: "primary",
        }
      : {
          size: "xs",
          variant: "outline",
        };

  return (
    <Button
        onClick={handleOpenButtonClicked}
        data-testid="add-property-btn"
        {...openButtonStyles}
      >
        {buttonLabel}
      </Button>
  );
};

export default AddProperty;
