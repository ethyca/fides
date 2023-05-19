import { Divider } from "@fidesui/react";
import React, { useMemo } from "react";
import { getConsentContext, resolveConsentValue } from "fides-js";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  changeConsent,
  selectFidesKeyToConsent,
} from "~/features/consent/consent.slice";
import { getGpcStatus } from "~/features/consent/helpers";

import { useConfig } from "~/features/common/config.slice";
import ConsentItem from "./ConsentItem";

const ConfigDrivenConsent = () => {
  const config = useConfig();
  const consentOptions = useMemo(
    () => config.consent?.page.consentOptions ?? [],
    [config]
  );
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
          ...option,
          value,
          gpcStatus,
        };
      }),
    [consentContext, consentOptions, fidesKeyToConsent]
  );
  return (
    <>
      {items.map((item, index) => {
        const { fidesDataUseKey, highlight, url, name, description } = item;
        const handleChange = (value: boolean) => {
          dispatch(changeConsent({ key: fidesDataUseKey, value }));
        };
        return (
          <React.Fragment key={fidesDataUseKey}>
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
