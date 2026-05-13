import type { System } from "~/types/api";

export type SystemInfoFormValues = Pick<System, "name" | "description">;
