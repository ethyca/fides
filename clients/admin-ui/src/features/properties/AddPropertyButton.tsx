import { AntButton as Button, AntButtonProps as ButtonProps } from "fidesui";
import { useRouter } from "next/router";

import { ADD_PROPERTY_ROUTE } from "~/features/common/nav/routes";

const AddPropertyButton = ({
  buttonLabel,
  buttonProps,
}: {
  buttonLabel?: string;
  buttonProps?: ButtonProps;
}) => {
  const router = useRouter();

  return (
    <Button
      onClick={() => router.push(ADD_PROPERTY_ROUTE)}
      data-testid="add-property-button"
      {...buttonProps}
    >
      {buttonLabel}
    </Button>
  );
};

export default AddPropertyButton;
