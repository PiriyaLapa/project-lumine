/**
 * CustomerProfileScreen — a customer's Purchase History and Follow-Up
 * History (2-2-2), toggled by chips. Store-wide within the staff member's
 * own store (see CLAUDE.md Auth Rules exception).
 * Data source: GET /api/v1/customers/{customer_id}, .../transactions, .../tasks.
 * Tap a Done follow-up row → EvidenceDetailScreen (reused, not rebuilt).
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
import { RouteProp, useFocusEffect } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import { THEME } from '../styles/theme';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'CustomerProfile'>;
  route: RouteProp<RootStackParamList, 'CustomerProfile'>;
};

type Tab = 'purchases' | 'followups';

const TASK_TYPE_LABELS: Record<string, string> = {
  '2D': 'Experience Check (T+2)',
  '2W': 'Relationship Building (T+14)',
  '2M': 'Retention Check (T+60)',
};

const STATUS_COLORS: Record<string, string> = {
  Pending: THEME.colors.statusPending,
  Done: THEME.colors.statusDone,
  Superseded: THEME.colors.statusSuperseded,
};

interface CustomerProfile {
  customer_id: string;
  name: string;
  do_not_contact: boolean;
  source: string;
}

interface CustomerTransaction {
  idoc_number: string;
  posting_date: string;
  material_desc: string | null;
  price: number | null;
  returned: boolean;
  staff_name: string | null;
}

interface CustomerTask {
  id: number;
  task_type: string;
  due_date: string;
  status: string;
  staff_name: string | null;
}

export default function CustomerProfileScreen({ navigation, route }: Props) {
  const { customer_id, customer_name } = route.params;
  const [tab, setTab] = useState<Tab>('purchases');
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [transactions, setTransactions] = useState<CustomerTransaction[]>([]);
  const [tasks, setTasks] = useState<CustomerTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useFocusEffect(
    useCallback(() => {
      fetchAll();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [customer_id])
  );

  const fetchAll = async () => {
    setLoading(true);
    setLoadError('');
    try {
      const [profileResp, txnResp, taskResp] = await Promise.all([
        client.get(`/api/v1/customers/${customer_id}`),
        client.get(`/api/v1/customers/${customer_id}/transactions`),
        client.get(`/api/v1/customers/${customer_id}/tasks`),
      ]);
      setProfile(profileResp.data);
      setTransactions(txnResp.data);
      setTasks(taskResp.data);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } };
      if (axiosErr.response?.status === 404) {
        setLoadError('No history found for this customer in your store.');
      } else {
        setLoadError('Failed to load customer history. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const renderTransaction = ({ item }: { item: CustomerTransaction }) => (
    <View style={styles.card}>
      <View style={styles.cardTop}>
        <Text style={styles.cardTitle} numberOfLines={1}>
          {item.material_desc ?? 'Unknown product'}
        </Text>
        {item.returned && (
          <View style={styles.returnedBadge}>
            <Text style={styles.returnedBadgeText}>Returned</Text>
          </View>
        )}
      </View>
      <Text style={styles.meta}>Purchased: {item.posting_date}</Text>
      {item.price != null && (
        <Text style={styles.meta}>Price: ฿{item.price.toLocaleString()}</Text>
      )}
      {!!item.staff_name && <Text style={styles.staffName}>Sold by: {item.staff_name}</Text>}
    </View>
  );

  const renderTask = ({ item }: { item: CustomerTask }) => (
    <TouchableOpacity
      style={styles.card}
      activeOpacity={item.status === 'Done' ? 0.75 : 1}
      disabled={item.status !== 'Done'}
      onPress={() => navigation.navigate('EvidenceDetail', { taskId: item.id })}
    >
      <View style={styles.cardTop}>
        <Text style={styles.cardTitle}>{TASK_TYPE_LABELS[item.task_type] ?? item.task_type}</Text>
        <View style={[styles.statusBadge, { backgroundColor: STATUS_COLORS[item.status] }]}>
          <Text style={styles.statusBadgeText}>{item.status}</Text>
        </View>
      </View>
      <Text style={styles.meta}>Due: {item.due_date}</Text>
      {!!item.staff_name && <Text style={styles.staffName}>Sold by: {item.staff_name}</Text>}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <View style={styles.headerText}>
          <Text style={styles.title} numberOfLines={1}>
            {profile?.name ?? customer_name ?? customer_id}
          </Text>
          <Text style={styles.subtitle}>Customer: {customer_id}</Text>
        </View>
      </View>

      <View style={styles.chipsRow}>
        <TouchableOpacity
          style={[styles.chip, tab === 'purchases' && styles.chipActive]}
          onPress={() => setTab('purchases')}
        >
          <Text style={[styles.chipText, tab === 'purchases' && styles.chipTextActive]}>
            Purchase History
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.chip, tab === 'followups' && styles.chipActive]}
          onPress={() => setTab('followups')}
        >
          <Text style={[styles.chipText, tab === 'followups' && styles.chipTextActive]}>
            Follow-Up History
          </Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <ActivityIndicator color={THEME.colors.primary} style={{ marginTop: 40 }} />
      ) : loadError ? (
        <Text style={styles.empty}>{loadError}</Text>
      ) : tab === 'purchases' ? (
        <FlatList
          data={transactions}
          keyExtractor={(item) => item.idoc_number}
          renderItem={renderTransaction}
          ListEmptyComponent={<Text style={styles.empty}>No purchases on record.</Text>}
          contentContainerStyle={styles.list}
        />
      ) : (
        <FlatList
          data={tasks}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderTask}
          ListEmptyComponent={<Text style={styles.empty}>No follow-up history yet.</Text>}
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
  headerText: { flex: 1 },
  title: { fontSize: THEME.fontSize.xl, fontWeight: '800', color: THEME.colors.text },
  subtitle: { fontSize: THEME.fontSize.sm, color: THEME.colors.textSecondary, marginTop: 2 },
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
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: THEME.spacing.xs,
    gap: THEME.spacing.sm,
  },
  cardTitle: { fontSize: THEME.fontSize.md, fontWeight: '700', color: THEME.colors.text, flex: 1 },
  meta: { fontSize: THEME.fontSize.sm, color: THEME.colors.textSecondary, marginTop: 2 },
  staffName: { fontSize: THEME.fontSize.sm, color: THEME.colors.soldBy, marginTop: 2 },
  returnedBadge: {
    backgroundColor: THEME.colors.error,
    borderRadius: THEME.radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  returnedBadgeText: { color: THEME.colors.card, fontSize: THEME.fontSize.xs, fontWeight: '700' },
  statusBadge: {
    borderRadius: THEME.radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  statusBadgeText: { color: THEME.colors.card, fontSize: THEME.fontSize.xs, fontWeight: '700' },
});
