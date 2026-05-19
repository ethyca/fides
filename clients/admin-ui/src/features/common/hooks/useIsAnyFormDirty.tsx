import { Form, useModal } from "fidesui";
import { createRef, MutableRefObject, useCallback, useEffect } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  registerForm,
  selectAnyDirtyForms,
  unregisterForm,
  updateDirtyFormState,
} from "~/features/common/hooks/dirty-forms.slice";

/*
 * There needs to be a global promise reference so ensure that
 * only one promise is active at the same time. Otherwise each
 * call instance `useIsAnyFormDirty` will have its reference.
 * Each call to `attemptAction` needs to return the same promise
 * in the event that multiple calls happen in quick succession.
 */
const modalResponsePromise = createRef() as MutableRefObject<
  Promise<boolean> | undefined
>;

type PromiseReturnFn = (value: boolean) => void;
const modalResolvePromise = createRef() as MutableRefObject<
  PromiseReturnFn | undefined
>;

export const useIsAnyFormDirty = () => {
  const anyDirtyForms = useAppSelector(selectAnyDirtyForms);
  const modal = useModal();

  const resetReferences = useCallback(() => {
    modalResolvePromise.current = undefined;
    modalResponsePromise.current = undefined;
  }, []);

  const attemptAction = useCallback(() => {
    if (anyDirtyForms) {
      /*
       * A new promise is only made when one isn't already in flight.
       * This is so that in the rare and unlikely event that two
       * different `attemptAction` calls happen at nearly the same time
       * they receive the same promise. This way when the user closes the
       * modal both calls correctly resolve at the same time.
       */
      if (!modalResponsePromise.current) {
        modalResponsePromise.current = new Promise((resolve) => {
          modalResolvePromise.current = resolve;
        });
        modal.confirm({
          title: "Unsaved Changes",
          content: "You have unsaved changes",
          centered: true,
          icon: null,
          okText: "Continue anyway",
          onOk: () => {
            if (modalResolvePromise.current) {
              modalResolvePromise.current(true);
              resetReferences();
            }
          },
          onCancel: () => {
            if (modalResolvePromise.current) {
              modalResolvePromise.current(false);
              resetReferences();
            }
          },
        });
      }
      return modalResponsePromise.current as Promise<boolean>;
    }
    return Promise.resolve(true);
  }, [anyDirtyForms, modal, resetReferences]);

  return {
    attemptAction,
  };
};

type FormGuardProps = {
  id: string;
  name: string;
};
export const FormGuard = ({ id, name }: FormGuardProps) => {
  const form = Form.useFormInstance();
  // useWatch re-renders this component on any field change so isFieldsTouched stays current
  Form.useWatch([], form);
  const dispatch = useAppDispatch();
  const isDirty = form.isFieldsTouched();

  useEffect(() => {
    dispatch(registerForm({ id, name }));

    return () => {
      dispatch(unregisterForm({ id }));
    };
  }, [dispatch, id, name]);

  useEffect(() => {
    dispatch(updateDirtyFormState({ id, isDirty }));
  }, [isDirty, dispatch, id]);

  return null;
};
