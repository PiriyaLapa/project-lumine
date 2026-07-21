/**
 * FollowUpDashboardScreen — Follow-Up Dashboard, all roles.
 * Data source: GET /api/v1/reports/dashboard?period=today|week|month|all.
 * sales_associate gets a single-row staff_breakdown (themselves); store_manager
 * gets a per-staff row for every active staff member in their store. Same
 * response shape for both — store_totals is always the headline summary card.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useFocusEffect } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import { THEME } from '../styles/theme';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'FollowUpDashboard'> };

type Period = 'today' | 'week' | 'month' | 'all';

const PERIOD_LABELS: Record<Period, string> = {
  today: 'Today',
  week: 'This Week',
  month: 'This Month',
  all: 'All Time',
};

interface StaffFollowUpStats {
  staff_id: number | null;
  staff_name: string | null;
  tasks_due: number;
  tasks_done: number;
  tasks_pending: number;
  tasks_skipped: number;
  messages_sent_line: number;
  messages_sent_email: number;
  customers_followed_up: number;
}

interface ManagerDashboardReport {
  store_id: number;
  period: Period;
  date_from: string | null;
  date_to: string | null;
  staff_breakdown: StaffFollowUpStats[];
  store_totals: StaffFollowUpStats;
}

export default function FollowUpDashboardScreen({ navigation }: Props) {
  const [period, setPeriod] = useState<Period>('today');
  const [data, setData] = useState<ManagerDashboardReport | null>(null);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      fetchDashboard();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [period])
  );

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const resp = await client.get('/api/v1/reports/dashboard', { params: { period } });
      setData(resp.data);
    } catch {
      // Network/auth error — show empty state
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const renderStaffRow = ({ item }: { item: StaffFollowUpStats }) => (
    <View style={styles.card}>
      {item.staff_name ? <Text style={styles.staffName}>{item.staff_name}</Text> : null}
      <View style={styles.statsRow}>
        <Text style={styles.statBadgeDone}>{item.tasks_done} done</Text>
        <Text style={styles.statBadgePending}>{item.tasks_pending} pending</Text>
        <Text style={styles.statBadgeMuted}>{item.tasks_skipped} skipped</Text>
      </View>
      <Text style={styles.meta}>
        Followed up: {item.customers_followed_up} customers
      </Text>
      <Text style={styles.meta}>
        LINE: {item.messages_sent_line} · Email: {item.messages_sent_email}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Follow-Up Report</Text>
      </View>

      <View style={styles.chipsRow}>
        {(Object.keys(PERIOD_LABELS) as Period[]).map((p) => (
          <TouchableOpacity
            key={p}
            style={[styles.chip, period === p && styles.chipActive]}
            onPress={() => setPeriod(p)}
          >
            <Text style={[styles.chipText, period === p && styles.chipTextActive]}>
              {PERIOD_LABELS[p]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading && !data ? (
        <ActivityIndicator color={THEME.colors.primary} style={{ marginTop: 40 }} />
      ) : !data ? (
        <Text style={styles.empty}>Could not load your follow-up report.</Text>
      ) : (
        <FlatList
          data={data.staff_breakdown}
          keyExtractor={(item) => String(item.staff_id ?? 'me')}
          renderItem={renderStaffRow}
          ListHeaderComponent={
            <View style={styles.totalsCard}>
              <Text style={styles.totalsHeadline}>
                {data.store_totals.customers_followed_up} customers followed up
              </Text>
              <View style={styles.statsRow}>
                <Text style={styles.statBadgeDone}>{data.store_totals.tasks_done} done</Text>
                <Text style={styles.statBadgePending}>{data.store_totals.tasks_pending} pending</Text>
                <Text style={styles.statBadgeMuted}>{data.store_totals.tasks_skipped} skipped</Text>
              </View>
              <Text style={styles.meta}>
                LINE: {data.store_totals.messages_sent_line} · Email: {data.store_totals.messages_sent_email}
              </Text>
              {data.staff_breakdown.length > 1 ? (
                <Text style={styles.sectionLabel}>By staff member</Text>
              ) : null}
            </View>
          }
          ListEmptyComponent={<Text style={styles.empty}>No follow-up data for this period.</Text>}
          contentContainerStyle={styles.list}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.colors.background },
  header: {
    paddingHorizontal: THEME.spacing.lg,
    paddingTop: 56,
    paddingBottom: THEME.spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: THEME.spacing.md,
  },
  backBtn: { paddingVertical: 4 },
  backText: { color: THEME.colors.primary, fontSize: THEME.fontSize.md, fontWeight: '600' },
  title: { fontSize: THEME.fontSize.xl, fontWeight: '800', color: THEME.colors.text },
  chipsRow: {
    flexDirection: 'row',
    gap: THEME.spacing.sm,
    paddingHorizontal: THEME.spacing.md,
    paddingBottom: THEME.spacing.sm,
  },
  chip: {
    backgroundColor: THEME.colors.card,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderWidth: 1,
    borderColor: THEME.colors.textMuted,
  },
  chipActive: { backgroundColor: THEME.colors.primary, borderColor: THEME.colors.primary },
  chipText: { color: THEME.colors.text, fontSize: THEME.fontSize.sm, fontWeight: '600' },
  chipTextActive: { color: THEME.colors.card },
  list: { padding: THEME.spacing.md, gap: THEME.spacing.sm },
  empty: {
    color: THEME.colors.textMuted,
    textAlign: 'center',
    marginTop: 60,
    fontSize: THEME.fontSize.lg,
  },
  totalsCard: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.md,
    padding: THEME.spacing.md,
    marginBottom: THEME.spacing.sm,
    shadowColor: THEME.colors.primaryShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
    elevation: 3,
  },
  totalsHeadline: {
    fontSize: THEME.fontSize.xl,
    fontWeight: '800',
    color: THEME.colors.primary,
    marginBottom: THEME.spacing.xs,
  },
  sectionLabel: {
    fontSize: THEME.fontSize.sm,
    fontWeight: '700',
    color: THEME.colors.textSecondary,
    marginTop: THEME.spacing.md,
  },
  card: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.md,
    padding: THEME.spacing.md,
    shadowColor: THEME.colors.primaryShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
    elevation: 3,
  },
  staffName: { fontSize: THEME.fontSize.md, fontWeight: '700', color: THEME.colors.text, marginBottom: THEME.spacing.xs },
  statsRow: { flexDirection: 'row', gap: THEME.spacing.sm, marginBottom: THEME.spacing.xs },
  statBadgeDone: {
    fontSize: THEME.fontSize.xs, fontWeight: '700', color: THEME.colors.card,
    backgroundColor: THEME.colors.statusDone, borderRadius: THEME.radius.sm,
    paddingHorizontal: 8, paddingVertical: 3,
  },
  statBadgePending: {
    fontSize: THEME.fontSize.xs, fontWeight: '700', color: THEME.colors.card,
    backgroundColor: THEME.colors.statusPending, borderRadius: THEME.radius.sm,
    paddingHorizontal: 8, paddingVertical: 3,
  },
  statBadgeMuted: {
    fontSize: THEME.fontSize.xs, fontWeight: '700', color: THEME.colors.card,
    backgroundColor: THEME.colors.statusSuperseded, borderRadius: THEME.radius.sm,
    paddingHorizontal: 8, paddingVertical: 3,
  },
  meta: { fontSize: THEME.fontSize.sm, color: THEME.colors.textSecondary, marginTop: 2 },
});
