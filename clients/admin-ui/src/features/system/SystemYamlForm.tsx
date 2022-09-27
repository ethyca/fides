import { useToast } from "@fidesui/react";
import { useRouter } from "next/router";

import { System } from "~/types/api";

import { successToastParams } from "../common/toast";
import YamlForm from "../YamlForm";
import { useCreateSystemMutation } from "./system.slice";

// handle the common case where everything is nested under a `system` key
interface NestedSystem {
  system: System[];
}
export function isSystemArray(value: unknown): value is NestedSystem {
  return (
    typeof value === "object" &&
    value != null &&
    "system" in value &&
    Array.isArray((value as any).system)
  );
}

const DESCRIPTION =
  "Get started creating your system by pasting your system YAML below! You may have received this YAML from a colleague or your Ethyca developer support engineer.";

const SystemYamlForm = () => {
  const [createSystem] = useCreateSystemMutation();
  const toast = useToast();
  const router = useRouter();

  const handleCreate = async (yaml: unknown) => {
    let system;
    if (isSystemArray(yaml)) {
      [system] = yaml.system;
    } else {
      system = yaml;
    }

    return createSystem(system);
  };

  const handleSuccess = () => {
    toast(successToastParams("Successfully loaded new system YAML"));
    router.push(`/system`);
  };

  return (
    <YamlForm<System>
      description={DESCRIPTION}
      submitButtonText="Create system"
      onCreate={handleCreate}
      onSuccess={handleSuccess}
    />
  );
};

export default SystemYamlForm;
