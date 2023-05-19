import { Divider } from "@fidesui/react";
import React, { useMemo } from "react";
import { getConsentContext, resolveConsentValue } from "fides-js";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  changeConsent,
  selectFidesKeyToConsent,
} from "~/features/consent/consent.slice";
import { getGpcStatus } from "~/features/consent/helpers";
import { ConfigConsentOption } from "~/types/config";

import ConsentItem from "./ConsentItem";

const ConfigDrivenConsent = ({
  consentOptions,
}: {
  consentOptions: ConfigConsentOption[];
}) => {
  const dispatch = useAppDispatch();
  const consentContext = useMemo(() => getConsentContext(), []);
  const fidesKeyToConsent = useAppSelector(selectFidesKeyToConsent);
  const items = useMemo(
    () =>
      consentOptions.map((option) => {
        const defaultValue = resolveConsentValue(
          option.default,
          consentContext
        );
        const value = fidesKeyToConsent[option.fidesDataUseKey] ?? defaultValue;
        const gpcStatus = getGpcStatus({
          value,
          consentOption: option,
          consentContext,
        });

        return {
          option,
          value,
          gpcStatus,
        };
      }),
    [consentContext, consentOptions, fidesKeyToConsent]
  );
  return (
    <>
      {items.map((item, index) => {
        const { fidesDataUseKey, highlight, url, name, description } =
          item.option;
        const handleChange = (value: boolean) => {
          dispatch(changeConsent({ option: item.option, value }));
        };
        return (
          <React.Fragment key={item.option.fidesDataUseKey}>
            {index > 0 ? <Divider /> : null}
            <ConsentItem
              id={fidesDataUseKey}
              name={name}
              description={description}
              highlight={highlight}
              url={url}
              value={item.value}
              gpcStatus={item.gpcStatus}
              onChange={handleChange}
            />
          </React.Fragment>
        );
      })}
    </>
  );
};

export default ConfigDrivenConsent;
