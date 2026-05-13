/**
 * TaskDetailScreen — task detail + action buttons.
 * SRS NFR-04: mark Done + log evidence in ≤ 3 taps from Dashboard.
 * Law 2 — Optimistic Update: mark Done immediately in UI.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import OfflineBanner from '../components/OfflineBanner';
import { THEME } from '../styles/theme';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'TaskDetail'>;
  route: RouteProp<RootStackParamList, 'TaskDetail'>;
};

const TASK_TYPE_LABELS: Record<string, string> = {
  '2D': 'Experience Check (T+2)',
  '2W': 'Relationship Building (T+14)',
  '2M': 'Retention Check (T+60)',
};

export default function TaskDetailScreen({ navigation, route }: Props) {
  const { taskId } = route.params;
  const [task, setTask] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState(false);

  useEffect(() => {
    fetchTask();
  }, [taskId]);

  const fetchTask = async () => {
    try {
      // GET /api/v1/tasks returns the full list; find the one we need
      const response = await client.get('/api/v1/tasks');
      const found = response.data.find((t: any) => t.id === taskId);
      setTask(found ?? null);
    } catch {
      // Use cached data if offline
    } finally {
      setLoading(false);
    }
  };

  // Law 2 — Optimistic Update with Rollback
  const handleMarkDone = async () => {
    if (!task) return;
    const previousStatus = task.status;
    setTask((prev: any) => ({ ...prev, status: 'Done' }));
    setMarking(true);

    try {
      await client.patch(`/api/v1/tasks/${taskId}`, { status: 'Done' });
    } catch {
      setTask((prev: any) => ({ ...prev, status: previousStatus }));
      Alert.alert('Sync Failed', 'Task not saved. Please retry.');
    } finally {
      setMarking(false);
    }
  };

  if (loading) return <ActivityIndicator style={{ flex: 1 }} color={THEME.colors.primary} />;
  if (!task) return (
    <View style={styles.container}>
      <Text style={styles.error}>Task not found.</Text>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      <OfflineBanner />

      <TouchableOpacity style={styles.back} onPress={() => navigation.goBack()}>
        <Text style={styles.backText}>← Back</Text>
      </TouchableOpacity>

      <View style={styles.card}>
        <Text style={styles.taskType}>{TASK_TYPE_LABELS[task.task_type]}</Text>
        <Text style={styles.field}>Customer ID: <Text style={styles.value}>{task.customer_id}</Text></Text>
        <Text style={styles.field}>Due Date: <Text style={styles.value}>{task.due_date}</Text></Text>
        <Text style={styles.field}>Status: <Text style={[styles.value, task.status === 'Done' && styles.done]}>{task.status}</Text></Text>
        <Text style={styles.field}>Calculated From: <Text style={styles.value}>{task.calculated_from}</Text></Text>
      </View>

      {task.status === 'Pending' && (
        <View style={styles.actions}>
          <TouchableOpacity
            style={styles.doneButton}
            onPress={handleMarkDone}
            disabled={marking}
          >
            <Text style={styles.doneText}>{marking ? 'Saving...' : '✓ Mark as Done'}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.evidenceButton}
            onPress={() => navigation.navigate('Evidence', { taskId })}
          >
            <Text style={styles.evidenceText}>📷 Log Evidence</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.barcodeButton}
            onPress={() => navigation.navigate('Barcode', { customer_id: task.customer_id })}
          >
            <Text style={styles.barcodeText}>Show Barcode</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.colors.background },
  back: { padding: 20, paddingTop: 56 },
  backText: { color: THEME.colors.primary, fontSize: 16 },
  card: {
    backgroundColor: THEME.colors.card,
    margin: 16,
    borderRadius: THEME.radius.md,
    padding: 20,
    shadowColor: THEME.colors.primaryShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  taskType: { fontSize: 20, fontWeight: '700', color: THEME.colors.text, marginBottom: 16 },
  field: { color: THEME.colors.textSecondary, fontSize: 14, marginBottom: 10 },
  value: { color: THEME.colors.text, fontWeight: '600' },
  done: { color: THEME.colors.success },
  actions: { padding: 16, gap: 12 },
  doneButton: { backgroundColor: THEME.colors.primary, borderRadius: 10, padding: 16, alignItems: 'center' },
  doneText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  evidenceButton: {
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: THEME.colors.primary,
    backgroundColor: 'transparent',
  },
  evidenceText: { color: THEME.colors.primary, fontSize: 16, fontWeight: '700' },
  barcodeButton: { backgroundColor: THEME.colors.surface, borderRadius: 10, padding: 16, alignItems: 'center' },
  barcodeText: { color: THEME.colors.text, fontSize: 16, fontWeight: '600' },
  error: { color: THEME.colors.error, textAlign: 'center', marginTop: 60, fontSize: 16 },
});
