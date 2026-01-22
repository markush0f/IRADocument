export type ServiceStatus = "ok" | "warn" | "fail";

export function summarize(status: ServiceStatus): string {
  return `Status: ${status}`;
}
