import { useFormikContext } from "formik";
import React, {
  createRef,
  MutableRefObject,
  useCallback,
  useEffect,
} from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  closeModal,
  openModal,
  registerForm,
  selectAnyDirtyForms,
  selectIsModalOpen,
  unregisterForm,
  updateDirtyFormState,
} from "~/features/common/hooks/dirty-forms.slice";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";

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

type BooleanReturnFn = (value: boolean) => boolean;
const modalResolvePromise = createRef() as MutableRefObject<
  BooleanReturnFn | undefined
>;

export const useIsAnyFormDirty = () => {
  const dispatch = useAppDispatch();

  const anyDirtyForms = useAppSelector(selectAnyDirtyForms);
  const resetReferences = useCallback(() => {
    modalResolvePromise.current = undefined;
    modalResponsePromise.current = undefined;
  }, []);
  const onConfirm = useCallback(() => {
    dispatch(closeModal());
    if (modalResolvePromise.current) {
      modalResolvePromise.current(true);
      resetReferences();
    }
  }, [dispatch, resetReferences]);

  const onClose = useCallback(() => {
    dispatch(closeModal());
    if (modalResolvePromise.current) {
      modalResolvePromise.current(false);
      resetReferences();
    }
  }, [dispatch, resetReferences]);

  const attemptAction = useCallback(() => {
    if (anyDirtyForms) {
      dispatch(openModal());
      /*
       * A new promise is only made when one isn't already in flight.
       * This is so that in the rare and unlikely event that two
       * different `attemptAction` calls happen at nearly the same time
       * they receive the same promise. This way when the user closes the
       * modal both calls correctly resolve at the same time.
       */
      if (!modalResponsePromise.current) {
        modalResponsePromise.current = new Promise(
          /*
           * This type is ignored for now because the type checker
           * isn't convinced that the `resolve` type is correct.
           * It is in practice. In the future it may be worth figuring
           * out exactly how to type this situation.
           */
          // @ts-ignore
          (resolve: (value: boolean) => boolean) => {
            modalResolvePromise.current = resolve;
          },
        );
      }
      return modalResponsePromise.current as Promise<boolean>;
    }
    return Promise.resolve(true);
  }, [anyDirtyForms, dispatch]);

  return {
    attemptAction,
    onConfirm,
    onClose,
  };
};

type FormGuardProps = {
  id: string;
  name: string;
};
export const FormGuard = ({ id, name }: FormGuardProps) => {
  const { dirty } = useFormikContext();
  const dispatch = useAppDispatch();

  useEffect(() => {
    // Provide info on active form
    dispatch(registerForm({ id, name }));

    return () => {
      // When un-rendered, remove from shared state.
      dispatch(unregisterForm({ id }));
    };
  }, [dispatch, id, name]);

  useEffect(() => {
    // Update shared state whenever the dirty state changes.
    dispatch(updateDirtyFormState({ id, isDirty: dirty }));
  }, [dirty, dispatch, id]);

  return null;
};

export const DirtyFormConfirmationModal = () => {
  const { onConfirm, onClose } = useIsAnyFormDirty();
  const isModalOpen = useAppSelector(selectIsModalOpen);
  return (
    <ConfirmationModal
      isOpen={isModalOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      isCentered
      title="Unsaved Changes"
      message="You have unsaved changes"
    />
  );
};
