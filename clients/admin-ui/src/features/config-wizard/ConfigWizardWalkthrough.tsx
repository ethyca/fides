import { Box, Button, CloseSolidIcon, Divider, Stack } from "@fidesui/react";
import HorizontalStepper from "common/HorizontalStepper";
import Stepper from "common/Stepper";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import DescribeSystemStep from "~/features/system/DescribeSystemStep";
import PrivacyDeclarationStep from "~/features/system/PrivacyDeclarationStep";
import ReviewSystemStep from "~/features/system/ReviewSystemStep";
import { System } from "~/types/api";

import AddSystem from "./AddSystem";
import AuthenticateScanner from "./AuthenticateScanner";
import {
  changeReviewStep,
  changeStep,
  reset,
  reviewManualSystem,
  selectReviewStep,
  selectStep,
  selectSystemInReview,
  selectSystemsForReview,
  setSystemInReview,
} from "./config-wizard.slice";
import { HORIZONTAL_STEPS, STEPS } from "./constants";
import OrganizationInfoForm from "./OrganizationInfoForm";
import ScanResults from "./ScanResults";
import SuccessPage from "./SuccessPage";

const ConfigWizardWalkthrough = () => {
  const dispatch = useAppDispatch();
  const step = useAppSelector(selectStep);
  const reviewStep = useAppSelector(selectReviewStep);
  const system = useAppSelector(selectSystemInReview);
  const systemsForReview = useAppSelector(selectSystemsForReview);
  const features = useFeatures();

  const handleCancelSetup = () => {
    dispatch(reset());
  };

  const handleSuccess = (values: System) => {
    dispatch(setSystemInReview(values));
    dispatch(changeReviewStep());
  };

  return (
    <>
      {!features.flags.navV2 && (
        <>
          <Box bg="white">
            <Button
              bg="transparent"
              fontWeight="500"
              m={2}
              ml={6}
              onClick={handleCancelSetup}
            >
              <CloseSolidIcon width="17px" /> Cancel setup
            </Button>
          </Box>
          <Divider orientation="horizontal" />
        </>
      )}
      <Stack direction={["column", "row"]}>
        <Stack bg="white" height="100vh" width="100%">
          <Stack
            mt={10}
            mb={10}
            direction="row"
            spacing="24px"
            justifyContent={
              features.flags.configWizardStepper ? undefined : "center"
            }
          >
            <Box flexShrink={0}>
              <Stepper
                activeStep={step}
                setActiveStep={(s) => dispatch(changeStep(s))}
                steps={STEPS}
              />
            </Box>
            <Box w={step === 4 ? "100%" : "40%"}>
              {step === 1 ? <OrganizationInfoForm /> : null}
              {step === 2 ? <AddSystem /> : null}
              {step === 3 ? <AuthenticateScanner /> : null}
              {step === 4 ? (
                <Box pr={10}>
                  <ScanResults />
                </Box>
              ) : null}
              {/* These steps should only apply if you're creating systems manually */}
              {step === 5 ? (
                <Stack direction="column">
                  {reviewStep <= 3 ? (
                    <HorizontalStepper
                      activeStep={reviewStep}
                      steps={HORIZONTAL_STEPS}
                    />
                  ) : null}
                  {reviewStep === 1 && (
                    <DescribeSystemStep
                      system={system}
                      onSuccess={handleSuccess}
                      abridged
                    />
                  )}
                  {reviewStep === 2 && system && (
                    <PrivacyDeclarationStep
                      system={system}
                      onSuccess={handleSuccess}
                      abridged
                    />
                  )}
                  {reviewStep === 3 && system && (
                    <ReviewSystemStep
                      system={system}
                      onSuccess={() => dispatch(changeReviewStep())}
                      abridged
                    />
                  )}
                  {reviewStep === 4 && system && (
                    <SuccessPage
                      systemInReview={system}
                      systemsForReview={systemsForReview}
                      onAddNextSystem={() => {
                        dispatch(reviewManualSystem());
                      }}
                    />
                  )}
                </Stack>
              ) : null}
            </Box>
          </Stack>
        </Stack>
      </Stack>
    </>
  );
};

export default ConfigWizardWalkthrough;
