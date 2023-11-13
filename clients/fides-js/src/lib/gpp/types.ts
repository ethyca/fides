export type GppFunction = (
  command: string,
  callback: (event: any, success: boolean) => void,
  parameter?: number | string,
  version?: string
) => void;
