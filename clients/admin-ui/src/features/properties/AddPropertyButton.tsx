import { Button, ButtonProps } from "@fidesui/react";
import { useRouter } from "next/router";

import { ADD_PROPERTY_ROUTE } from "~/features/common/nav/v2/routes";

type ButtonVariant = "primary" | "outline";

const AddPropertyButton = ({
  buttonLabel,
  buttonVariant = "primary",
}: {
  buttonLabel?: string;
  buttonVariant?: ButtonVariant;
}) => {
  const router = useRouter();
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
      onClick={() => router.push(ADD_PROPERTY_ROUTE)}
      data-testid="add-property-btn"
      {...openButtonStyles}
    >
      {buttonLabel}
    </Button>
  );
};

export default AddPropertyButton;
