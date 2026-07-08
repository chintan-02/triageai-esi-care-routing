export type ClinicianRole = 'Nurse' | 'Doctor' | 'Admin';

export interface AuthUser {
  name: string;
  role: ClinicianRole;
  initials: string;
  email?: string;
  organization?: string;
  unit?: string;
}

export interface RegisterAccountInput {
  name: string;
  email: string;
  organization: string;
  unit: string;
  role: ClinicianRole;
  password: string;
}
