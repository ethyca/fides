export interface AlertState {
  status: 'error' | 'success' | 'info' | 'warning';
  description: string;
}
