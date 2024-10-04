import { AntButton, AntButtonProps } from "fidesui";
import { useRouter } from "next/router";

import { ADD_PROPERTY_ROUTE } from "~/features/common/nav/v2/routes";

const AddPropertyButton = ({
  buttonLabel,
  buttonProps,
}: {
  buttonLabel?: string;
  buttonProps?: AntButtonProps;
}) => {
  const router = useRouter();

  return (
    <AntButton
      onClick={() => router.push(ADD_PROPERTY_ROUTE)}
      data-testid="add-property-button"
      {...buttonProps}
    >
      {buttonLabel}
    </AntButton>
  );
};

export default AddPropertyButton;
