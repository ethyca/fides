import { Flex, Typography, useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { useUpdateSystemMutation } from "~/features/system/system.slice";
import {
  PrivacyDeclarationResponse,
  System,
  SystemResponse,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

import SimplifiedPrivacyDeclarationAccordion from "./SimplifiedPrivacyDeclarationAccordion";
import { DataProps } from "./SimplifiedPrivacyDeclarationForm";

interface Props {
  system: SystemResponse;
  onSave?: (system: System) => void;
}

const SimplifiedPrivacyDeclarationManager = ({
  system,
  onSave,
  ...dataProps
}: Props & DataProps) => {
  const message = useMessage();
  const [updateSystemMutationTrigger] = useUpdateSystemMutation();

  const handleEditDeclaration = async (
    oldDeclaration: PrivacyDeclarationResponse,
    updatedDeclaration: PrivacyDeclarationResponse,
  ) => {
    if (
      updatedDeclaration.id !== oldDeclaration.id &&
      system.privacy_declarations.some(
        (d) =>
          d.data_use === updatedDeclaration.data_use &&
          d.name === updatedDeclaration.name,
      )
    ) {
      message.error(
        "A declaration already exists with that data use in this system. Please supply a different data use.",
      );
      return undefined;
    }

    const transformedDeclarations = system.privacy_declarations
      .map((dec) => (dec.id === oldDeclaration.id ? updatedDeclaration : dec))
      .map((d) => ({ ...d, name: d.name ?? "" }));

    const result = await updateSystemMutationTrigger({
      ...system,
      privacy_declarations: transformedDeclarations,
    });

    if (isErrorResult(result)) {
      message.error(
        getErrorMessage(
          result.error,
          "An unexpected error occurred while updating the system. Please try again.",
        ),
      );
      return undefined;
    }
    message.destroy();
    message.success("Data use saved");
    onSave?.(result.data);
    return result.data.privacy_declarations;
  };

  return (
    <Flex vertical gap="small">
      <SimplifiedPrivacyDeclarationAccordion
        privacyDeclarations={system.privacy_declarations}
        onEdit={handleEditDeclaration}
        {...dataProps}
      />
      {system.privacy_declarations.length === 0 ? (
        <Typography.Text size="sm">No data uses</Typography.Text>
      ) : null}
    </Flex>
  );
};

export default SimplifiedPrivacyDeclarationManager;
