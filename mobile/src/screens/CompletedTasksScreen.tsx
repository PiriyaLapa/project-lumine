/**
 * CompletedTasksScreen — list of tasks with status "Done".
 * Data source: GET /api/v1/tasks (same endpoint as Dashboard),
 * filtered client-side for status === 'Done'.
 * Tap a row → EvidenceDetailScreen to view/edit evidence.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useFocusEffect } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import { THEME } from '../styles/theme';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'CompletedTasks'> };

const TASK_TYPE_LABELS: Record<string, string> = {
  '2D': 'Experience Check (T+2)',
  '2W': 'Relationship Building (T+14)',
  '2M': 'Retention Check (T+60)',
};

interface DoneTask {
  id: number;
  customer_id: string;
  task_type: string;
  due_date: string;
  status: string;
  staff_name: string | null;
  updated_at: string;
}

export default function CompletedTasksScreen({ navigation }: Props) {
  const [tasks, setTasks] = useState<DoneTask[]>([]);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      fetchDoneTasks();
    }, [])
  );

  const fetchDoneTasks = async () => {
    setLoading(true);
    try {
      const resp = await client.get('/api/v1/tasks');
      const done: DoneTask[] = resp.data.filter((t: DoneTask) => t.status === 'Done');
      // Most recently completed first
      done.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
      setTasks(done);
    } catch {
      // Network error — show empty state
    } finally {
      setLoading(false);
    }
  };

  const renderItem = ({ item }: { item: DoneTask }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('EvidenceDetail', { taskId: item.id })}
      activeOpacity={0.75}
    >
      <View style={styles.cardTop}>
        <Text style={styles.taskType}>
          {TASK_TYPE_LABELS[item.task_type] ?? item.task_type}
        </Text>
        <View style={styles.doneBadge}>
          <Text style={styles.doneBadgeText}>Done</Text>
        </View>
      </View>
      <TouchableOpacity
        onPress={() =>
          navigation.navigate('CustomerProfile', { customer_id: item.customer_id, customer_name: null })
        }
        hitSlop={{ top: 4, bottom: 4, left: 4, right: 4 }}
      >
        <Text style={[styles.meta, styles.customerLink]}>Customer: {item.customer_id}</Text>
      </TouchableOpacity>
      <Text style={styles.meta}>Due: {item.due_date}</Text>
      {item.staff_name ? (
        <Text style={styles.staffName}>Sold by: {item.staff_name}</Text>
      ) : null}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Completed Tasks</Text>
      </View>

      {loading ? (
        <ActivityIndicator color={THEME.colors.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={tasks}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={fetchDoneTasks}
              tintColor={THEME.colors.primary}
            />
          }
          ListEmptyComponent={
            <Text style={styles.empty}>No completed tasks yet.</Text>
          }
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
  },
  taskType: { fontSize: THEME.fontSize.md, fontWeight: '700', color: THEME.colors.text, flex: 1 },
  doneBadge: {
    backgroundColor: THEME.colors.statusDone,
    borderRadius: THEME.radius.sm,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  doneBadgeText: { color: THEME.colors.card, fontSize: THEME.fontSize.xs, fontWeight: '700' },
  meta: { fontSize: THEME.fontSize.sm, color: THEME.colors.textSecondary, marginTop: 2 },
  customerLink: { color: THEME.colors.primary, fontWeight: '600' },
  staffName: { fontSize: THEME.fontSize.sm, color: THEME.colors.soldBy, marginTop: 2 },
});
