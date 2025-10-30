import React from "react";

import { PrivacyRequestResponse } from "~/types/api";

import { LabeledTag, LabeledText } from "./labels";

export const EmailIdentity = ({ value }: { value?: string | null }) => {
  return (value ?? "").length > 0 ? (
    <LabeledText label="Email">{value}</LabeledText>
  ) : null;
};

export const NonEmailIdentities = ({
  identities,
}: {
  identities: PrivacyRequestResponse["identity"];
}) => {
  return (
    <>
      {Object.entries(identities)
        .filter(([key, identity]) => identity.value && key !== "email")
        .map(([key, identity]) => (
          <LabeledTag key={key} label={identity.label}>
            {identity.value}
          </LabeledTag>
        ))}
    </>
  );
};
