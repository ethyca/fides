import { useDisclosure } from "@fidesui/react";

import PickerCard, {
  NUM_TO_SHOW,
  Props as PickerCardProps,
} from "~/features/common/PickerCard";
import { LocationRegulationBase } from "~/types/api";

import RegulationModal from "./RegulationModal";

const RegulationPickerCard = ({
  title,
  items,
  selected,
  onChange,
}: Pick<
  PickerCardProps<LocationRegulationBase>,
  "title" | "items" | "selected" | "onChange"
>) => {
  const disclosure = useDisclosure();

  return (
    <>
      <PickerCard
        title={title}
        items={items}
        selected={selected}
        onChange={onChange}
        numSelected={selected.length}
        indeterminate={[]}
        onViewMore={items.length > NUM_TO_SHOW ? disclosure.onOpen : undefined}
      />
      <RegulationModal
        regulations={items}
        isOpen={disclosure.isOpen}
        onClose={disclosure.onClose}
        selected={selected}
        onChange={onChange}
      />
    </>
  );
};

export default RegulationPickerCard;
