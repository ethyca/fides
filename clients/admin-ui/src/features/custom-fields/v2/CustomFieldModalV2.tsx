import { AntModal, AntModalProps } from "fidesui";

import { CustomFieldDefinitionWithId } from "~/types/api";

interface CustomFieldModalV2Props extends AntModalProps {
  field?: CustomFieldDefinitionWithId;
}

const CustomFieldModalV2 = ({ field, ...props }: CustomFieldModalV2Props) => {
  return (
    <AntModal
      {...props}
      width="768px"
      title={field ? `Edit ${field.name}` : "Add custom field"}
    >
      test
    </AntModal>
  );
};

export default CustomFieldModalV2;
