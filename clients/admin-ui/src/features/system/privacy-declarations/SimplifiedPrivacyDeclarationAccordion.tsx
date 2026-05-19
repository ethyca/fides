import { Collapse, CollapseProps } from "fidesui";
import { useState } from "react";

import { DataUse, PrivacyDeclarationResponse } from "~/types/api";

import {
  DataProps,
  SavedIndicator,
  SimplifiedPrivacyDeclarationForm,
} from "./SimplifiedPrivacyDeclarationForm";

interface AccordionProps extends DataProps {
  privacyDeclarations: PrivacyDeclarationResponse[];
  onEdit: (
    oldDeclaration: PrivacyDeclarationResponse,
    newDeclaration: PrivacyDeclarationResponse,
  ) => Promise<PrivacyDeclarationResponse[] | undefined>;
}

const getDeclarationTitle = (
  declaration: PrivacyDeclarationResponse,
  allDataUses: DataUse[],
) => {
  const matched = allDataUses.find(
    (du) => du.fides_key === declaration.data_use,
  );
  if (!matched) {
    return declaration.data_use;
  }
  return declaration.name
    ? `${matched.name} - ${declaration.name}`
    : matched.name;
};

const SimplifiedPrivacyDeclarationAccordion = ({
  privacyDeclarations,
  onEdit,
  allDataUses,
  ...dataProps
}: AccordionProps) => {
  const [savedById, setSavedById] = useState<Record<string, boolean>>({});

  const setSavedFor = (id: string, saved: boolean) => {
    setSavedById((prev) => {
      if (prev[id] === saved) {
        return prev;
      }
      return { ...prev, [id]: saved };
    });
  };

  const items: CollapseProps["items"] = privacyDeclarations.map(
    (declaration) => ({
      key: declaration.id,
      label: getDeclarationTitle(declaration, allDataUses),
      extra: savedById[declaration.id] ? <SavedIndicator /> : null,
      "data-testid": `accordion-header-${declaration.data_use}`,
      children: (
        <SimplifiedPrivacyDeclarationForm
          initialValues={declaration}
          privacyDeclarationId={declaration.id}
          allDataUses={allDataUses}
          onSubmit={(values) => onEdit(declaration, values)}
          onSavedChange={(saved) => setSavedFor(declaration.id, saved)}
          {...dataProps}
        />
      ),
    }),
  );

  return (
    <Collapse
      accordion
      bordered={false}
      items={items}
      data-testid="privacy-declaration-accordion"
    />
  );
};

export default SimplifiedPrivacyDeclarationAccordion;
