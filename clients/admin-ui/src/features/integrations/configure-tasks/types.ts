// This file can be removed - we're now using the generated API types:
// ManualTaskFieldType, ManualFieldRequestType, etc.

// Keeping this file for now to avoid breaking imports, but it can be cleaned up later
export enum TaskInputType {
  STRING = "string",
  FILE = "file",
  CHECKBOX = "checkbox",
}

export const TASK_INPUT_TYPE_LABELS: Record<TaskInputType, string> = {
  [TaskInputType.STRING]: "Text",
  [TaskInputType.FILE]: "File",
  [TaskInputType.CHECKBOX]: "Checkbox",
};

export const TASK_INPUT_TYPE_OPTIONS = [
  {
    label: TASK_INPUT_TYPE_LABELS[TaskInputType.STRING],
    value: TaskInputType.STRING,
  },
  {
    label: TASK_INPUT_TYPE_LABELS[TaskInputType.FILE],
    value: TaskInputType.FILE,
  },
  {
    label: TASK_INPUT_TYPE_LABELS[TaskInputType.CHECKBOX],
    value: TaskInputType.CHECKBOX,
  },
];
