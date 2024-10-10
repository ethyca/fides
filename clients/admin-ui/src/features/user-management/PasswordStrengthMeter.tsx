import type { StackProps } from "@chakra-ui/react";
import { Box, color, HStack, Stack } from "@chakra-ui/react";
import { forwardRef } from "react";
import { passwordValidation } from "../common/form/validation";
import {
  commonPasswords,
  PasswordStrength,
  PasswordStrengthStatistics,
  trigraphs,
} from "tai-password-strength";

interface PasswordStrengthMeterProps extends StackProps {
  maxSegments?: number;
  password: string;
}

const StrongEntropy = 80;

function getEntropy(passwordStrength: PasswordStrengthStatistics) {
  return (
    passwordStrength.trigraphEntropyBits ??
    passwordStrength.shannonEntropyBits ??
    0
  );
}

export const PasswordStrengthMeter = forwardRef<
  HTMLDivElement,
  PasswordStrengthMeterProps
>(function PasswordStrengthMeter(props, ref) {
  const { maxSegments = 4, password, ...rest } = props;

  const strengthTester = new PasswordStrength();
  const strength = strengthTester
    .addCommonPasswords(commonPasswords)
    .addTrigraphMap(trigraphs)
    .check(password);

  const percent = Math.min(getEntropy(strength), StrongEntropy) / StrongEntropy;
  const segments = strength.commonPassword ? 1 : percent * maxSegments;
  const { backgroundColor } = getColor(strength, maxSegments);
  return (
    <Stack align="flex-end" gap="1" ref={ref} {...rest}>
      <HStack width="full" ref={ref} {...rest}>
        {Array.from({ length: maxSegments }).map((_, index) => (
          <Box
            key={index}
            height="1"
            flex="1"
            rounded="sm"
            data-selected={index < segments ? "" : undefined}
            layerStyle="fill.subtle"
            _selected={{
              backgroundColor: backgroundColor,
              layerStyle: "fill.solid",
            }}
          />
        ))}
      </HStack>
    </Stack>
  );
});

function getColor(
  passwordStrength: PasswordStrengthStatistics,
  maxSegments: number,
) {
  const percent =
    Math.min(getEntropy(passwordStrength), StrongEntropy) / StrongEntropy; // TODO: duplicated code
  let hue = Math.floor(percent * 120);

  // Anything in the first segment should be fully red.
  if (percent < 1 / maxSegments || passwordStrength.commonPassword) {
    hue = 0;
  }

  const saturation = "90%";
  const lightness = "50%";
  return {
    backgroundColor: `hsl(${hue}, ${saturation}, ${lightness})`,
  };
}
