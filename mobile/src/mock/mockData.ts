/**
 * Mock data for DEV_MODE UI testing.
 * All field names match openapi.yaml schemas exactly — LOCKED.
 * Use these credentials on LoginScreen: benz@lumine.com / benz123
 */

import { CachedTask } from '../cache/offlineCache';

// ---------------------------------------------------------------------------
// Auth — openapi.yaml AuthResponse
// ---------------------------------------------------------------------------

export const MOCK_CREDENTIALS = {
  email: 'benz@lumine.com',
  password: 'benz123',
};

export const MOCK_AUTH_RESPONSE = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
  staff_id: 1,
  role: 'sales_associate',
};

export const MOCK_REFRESH_RESPONSE = {
  access_token: 'mock-access-token-refreshed',
  token_type: 'bearer',
};

// ---------------------------------------------------------------------------
// Tasks — openapi.yaml FollowUpTask schema
// ---------------------------------------------------------------------------

export const MOCK_TASKS: CachedTask[] = [
  {
    id: 1,
    customer_id: 'CUST-00123',
    task_type: '2D',
    task_basis: 'posting_date',
    due_date: '2026-04-22',
    calculated_from: '2026-04-20',
    status: 'Pending',
    staff_name: 'Benz',
    created_at: '2026-04-20T09:00:00',
    updated_at: '2026-04-20T09:00:00',
  },
  {
    id: 2,
    customer_id: 'CUST-00456',
    task_type: '2W',
    task_basis: 'posting_date',
    due_date: '2026-05-04',
    calculated_from: '2026-04-20',
    status: 'Pending',
    staff_name: 'Ann',
    created_at: '2026-04-20T09:00:00',
    updated_at: '2026-04-20T09:00:00',
  },
  {
    id: 3,
    customer_id: 'CUST-00789',
    task_type: '2M',
    task_basis: 'posting_date',
    due_date: '2026-06-19',
    calculated_from: '2026-04-20',
    status: 'Pending',
    staff_name: 'Benz',
    created_at: '2026-04-20T09:00:00',
    updated_at: '2026-04-20T09:00:00',
  },
  {
    id: 4,
    customer_id: 'CUST-00222',
    task_type: '2D',
    task_basis: 'posting_date',
    due_date: '2026-04-19',       // overdue — tests overdue highlight in TaskCard
    calculated_from: '2026-04-17',
    status: 'Pending',
    staff_name: 'Ann',
    created_at: '2026-04-17T10:00:00',
    updated_at: '2026-04-17T10:00:00',
  },
];

// ---------------------------------------------------------------------------
// Upload — openapi.yaml UploadResponse
// ---------------------------------------------------------------------------

export const MOCK_UPLOAD_RESPONSE = {
  tasks_created: 9,
  customers_processed: 3,
  cycles_reset: 1,
  errors: [],
};

// ---------------------------------------------------------------------------
// Evidence — openapi.yaml EvidenceResponse
// ---------------------------------------------------------------------------

export const MOCK_EVIDENCE_RESPONSE = {
  id: 101,
  task_id: 1,
  notes: 'Customer was happy with the product. Will follow up in two weeks.',
  image_uri: null,
  image_size_kb: null,
  timestamp: '2026-04-20T12:00:00',
};

// ---------------------------------------------------------------------------
// KPI — openapi.yaml KPIReport
// ---------------------------------------------------------------------------

export const MOCK_KPI_REPORT = {
  staff_id: 1,
  store_id: 1,
  total_tasks: 12,
  completed_tasks: 8,
  completion_rate: 0.667,
};

// ---------------------------------------------------------------------------
// Upload History — openapi.yaml UploadLog schema
// ---------------------------------------------------------------------------

export interface UploadLog {
  id: number;
  store_id: number;
  staff_id: number;
  filename: string;
  uploaded_at: string;
  row_count: number;
  tasks_created: number;
  date_range_start: string;
  date_range_end: string;
  status: 'success' | 'error';
}

export const MOCK_UPLOAD_HISTORY: UploadLog[] = [
  {
    id: 2,
    store_id: 8901,
    staff_id: 1,
    filename: 'sap_may.csv',
    uploaded_at: '2026-05-10T14:30:00',
    row_count: 27,
    tasks_created: 27,
    date_range_start: '2026-04-01',
    date_range_end: '2026-04-30',
    status: 'success',
  },
  {
    id: 1,
    store_id: 8901,
    staff_id: 1,
    filename: 'sap_jan_mar.csv',
    uploaded_at: '2026-04-01T09:00:00',
    row_count: 42,
    tasks_created: 42,
    date_range_start: '2026-01-01',
    date_range_end: '2026-03-31',
    status: 'success',
  },
];
