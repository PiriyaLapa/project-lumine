/**
 * Follow-Up Dashboard → PDF export + share.
 * Builds a self-contained HTML document from the already-fetched dashboard
 * data (no network calls here) and hands it to expo-print / expo-sharing.
 */

import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { THEME } from '../styles/theme';
import type { ManagerDashboardReport, StaffFollowUpStats } from '../screens/FollowUpDashboardScreen';

export class SharingUnavailableError extends Error {}

function formatDateRange(dateFrom: string | null, dateTo: string | null): string {
  if (!dateFrom && !dateTo) return 'All time';
  return `${dateFrom ?? '—'} to ${dateTo ?? '—'}`;
}

function staffRowHtml(row: StaffFollowUpStats): string {
  return `
    <tr>
      <td>${row.staff_name ?? '—'}</td>
      <td class="num">${row.tasks_done}</td>
      <td class="num">${row.tasks_pending}</td>
      <td class="num">${row.tasks_skipped}</td>
      <td class="num">${row.customers_followed_up}</td>
      <td class="num">${row.messages_sent_line}</td>
      <td class="num">${row.messages_sent_email}</td>
    </tr>`;
}

function staffSectionHtml(breakdown: StaffFollowUpStats[]): string {
  if (breakdown.length === 0) {
    return `<p class="empty">No staff activity in this period.</p>`;
  }
  if (breakdown.length <= 1) {
    // Associate view (or a single-staff store) — the totals card above is
    // already this person's own numbers, a 1-row table would be redundant.
    return '';
  }
  return `
    <h2>By Staff Member</h2>
    <table>
      <thead>
        <tr>
          <th>Staff</th><th class="num">Done</th><th class="num">Pending</th>
          <th class="num">Skipped</th><th class="num">Followed Up</th>
          <th class="num">LINE</th><th class="num">Email</th>
        </tr>
      </thead>
      <tbody>${breakdown.map(staffRowHtml).join('')}</tbody>
    </table>`;
}

export function buildDashboardHtml(data: ManagerDashboardReport, periodLabel: string): string {
  const { store_totals, staff_breakdown } = data;
  const generatedOn = new Date().toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return `
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  body {
    font-family: -apple-system, Roboto, sans-serif;
    background: ${THEME.colors.background};
    color: ${THEME.colors.text};
    padding: ${THEME.spacing.lg}px;
  }
  .brand {
    color: ${THEME.colors.primary};
    font-size: ${THEME.fontSize.brand}px;
    font-weight: 800;
    margin: 0;
  }
  .subtitle {
    font-size: ${THEME.fontSize.xl}px;
    font-weight: 700;
    margin: 0 0 ${THEME.spacing.sm}px 0;
  }
  .meta {
    color: ${THEME.colors.textSecondary};
    font-size: ${THEME.fontSize.sm}px;
    margin: 2px 0;
  }
  .card {
    background: ${THEME.colors.card};
    border-radius: ${THEME.radius.md}px;
    padding: ${THEME.spacing.md}px;
    margin-top: ${THEME.spacing.lg}px;
  }
  .headline {
    color: ${THEME.colors.primary};
    font-size: ${THEME.fontSize.xl}px;
    font-weight: 800;
    margin: 0 0 ${THEME.spacing.xs}px 0;
  }
  .staff-name {
    font-size: ${THEME.fontSize.md}px;
    font-weight: 700;
    margin: 0 0 ${THEME.spacing.xs}px 0;
  }
  .badges { margin: ${THEME.spacing.xs}px 0; }
  .badge {
    display: inline-block;
    color: ${THEME.colors.card};
    font-size: ${THEME.fontSize.xs}px;
    font-weight: 700;
    border-radius: ${THEME.radius.sm}px;
    padding: 3px 8px;
    margin-right: ${THEME.spacing.xs}px;
  }
  .badge-done { background: ${THEME.colors.statusDone}; }
  .badge-pending { background: ${THEME.colors.statusPending}; }
  .badge-skipped { background: ${THEME.colors.statusSuperseded}; }
  h2 {
    font-size: ${THEME.fontSize.lg}px;
    color: ${THEME.colors.textSecondary};
    margin-top: ${THEME.spacing.lg}px;
  }
  table { width: 100%; border-collapse: collapse; margin-top: ${THEME.spacing.sm}px; }
  th, td {
    text-align: left;
    padding: ${THEME.spacing.xs}px ${THEME.spacing.sm}px;
    border-bottom: 1px solid ${THEME.colors.divider};
    font-size: ${THEME.fontSize.sm}px;
  }
  th { color: ${THEME.colors.textSecondary}; }
  .num { text-align: right; }
  .empty { color: ${THEME.colors.textMuted}; margin-top: ${THEME.spacing.md}px; }
  .footer {
    color: ${THEME.colors.textMuted};
    font-size: ${THEME.fontSize.xs}px;
    margin-top: ${THEME.spacing.xl}px;
  }
</style>
</head>
<body>
  <p class="brand">LUMINE</p>
  <p class="subtitle">Follow-Up Report</p>
  <p class="meta">${periodLabel} · ${formatDateRange(data.date_from, data.date_to)}</p>
  <p class="meta">Generated on ${generatedOn}</p>

  <div class="card">
    ${store_totals.staff_name ? `<p class="staff-name">${store_totals.staff_name}</p>` : ''}
    <p class="headline">${store_totals.customers_followed_up} customers followed up</p>
    <div class="badges">
      <span class="badge badge-done">${store_totals.tasks_done} done</span>
      <span class="badge badge-pending">${store_totals.tasks_pending} pending</span>
      <span class="badge badge-skipped">${store_totals.tasks_skipped} skipped</span>
    </div>
    <p class="meta">LINE: ${store_totals.messages_sent_line} · Email: ${store_totals.messages_sent_email}</p>
  </div>

  ${staffSectionHtml(staff_breakdown)}

  <p class="footer">Lumine — Generated from the mobile app</p>
</body>
</html>`;
}

export async function generateAndShareDashboardPdf(
  data: ManagerDashboardReport,
  periodLabel: string
): Promise<void> {
  const html = buildDashboardHtml(data, periodLabel);
  const { uri } = await Print.printToFileAsync({ html });

  const canShare = await Sharing.isAvailableAsync();
  if (!canShare) {
    throw new SharingUnavailableError('Sharing is not available on this device.');
  }

  await Sharing.shareAsync(uri, {
    mimeType: 'application/pdf',
    dialogTitle: 'Share Follow-Up Report',
  });
}
