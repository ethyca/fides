import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { useUpsertSystemsMutation } from "~/features/system/system.slice";
import { System } from "~/types/api";
import { isErrorResult, RTKResult } from "~/types/errors";

const useShowHideSystems = () => {
  const [upsertSystems] = useUpsertSystemsMutation();

  const toast = useToast();

  const handleResult = (result: RTKResult, isMultiple?: boolean) => {
    if (isErrorResult(result)) {
      const errorMsg = getErrorMessage(
        result.error,
        `An unexpected error occurred while updating the ${isMultiple ? "systems" : "system"}. Please try again.`,
      );
      toast({ status: "error", description: errorMsg });
    } else {
      toast({
        status: "success",
        description: `${isMultiple ? "Systems" : "System"} updated successfully`,
      });
    }
  };

  const hideSystem = async (system: System) => {
    const result = await upsertSystems([
      {
        ...system,
        description: "I've been hidden!",
        hidden: true,
      },
    ]);
    handleResult(result);
  };

  const showSystem = async (system: System) => {
    const result = await upsertSystems([
      {
        ...system,
        hidden: false,
      },
    ]);
    handleResult(result);
  };

  const hideMultipleSystems = async (systems: System[]) => {
    const newSystems = systems.map((system) => ({
      ...system,
      hidden: true,
    }));

    const result = await upsertSystems(newSystems);
    handleResult(result, true);
  };

  const showMultipleSystems = async (systems: System[]) => {
    const newSystems = systems.map((system) => ({
      ...system,
      hidden: false,
    }));

    const result = await upsertSystems(newSystems);
    handleResult(result, true);
  };

  return {
    hideSystem,
    showSystem,
    hideMultipleSystems,
    showMultipleSystems,
  };
};

export default useShowHideSystems;
