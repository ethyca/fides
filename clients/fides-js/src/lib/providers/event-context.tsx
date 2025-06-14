import { createContext, h } from "preact";
import { MutableRefObject, ReactNode } from "preact/compat";
import { useCallback, useContext, useMemo, useRef } from "preact/hooks";

import { FidesCookie } from "../consent-types";
import {
  dispatchFidesEvent,
  FidesEventDetailsTrigger,
  FidesEventExtraDetails,
  FidesEventType,
} from "../events";

interface UseEventProps {
  triggerRef: MutableRefObject<FidesEventDetailsTrigger>;
  setTrigger: (newValue: FidesEventDetailsTrigger) => void;
  dispatchFidesEventAndClearTrigger: (
    type: FidesEventType,
    fidesCookie: FidesCookie | undefined,
    extraDetails?: FidesEventExtraDetails,
  ) => void;
}

const EventContext = createContext<UseEventProps | Record<any, never>>({});

export const EventProvider = ({ children }: { children: ReactNode }) => {
  const triggerRef = useRef<FidesEventDetailsTrigger>();

  const updateContextValue = useCallback(
    (newValue: FidesEventDetailsTrigger) => {
      triggerRef.current = newValue;
    },
    [],
  );

  const dispatchFidesEventAndClearTrigger = useCallback(
    (
      type: FidesEventType,
      fidesCookie: FidesCookie | undefined,
      extraDetails?: FidesEventExtraDetails,
    ) => {
      dispatchFidesEvent(type, fidesCookie, {
        ...extraDetails,
        trigger: {
          ...(extraDetails?.trigger as FidesEventDetailsTrigger),
          ...triggerRef.current,
        },
      });
      // Clear the trigger after dispatching
      updateContextValue(undefined);
    },
    [updateContextValue],
  );

  const value: UseEventProps = useMemo(
    () => ({
      triggerRef,
      setTrigger: updateContextValue,
      dispatchFidesEventAndClearTrigger,
    }),
    [updateContextValue, dispatchFidesEventAndClearTrigger],
  );

  return (
    <EventContext.Provider value={value}>{children}</EventContext.Provider>
  );
};

export const useEvent = () => {
  const context = useContext(EventContext);
  if (!context || Object.keys(context).length === 0) {
    throw new Error("useEvent must be used within a EventProvider");
  }
  return context as UseEventProps;
};
