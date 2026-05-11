/**
 * DashboardScreen — today's task list.
 *
 * UI State Management Laws (SRS §14):
 * Law 1 — Pull on Focus: fetch fresh tasks on every foreground event.
 * Law 2 — Optimistic Update with Rollback: mark Done immediately, revert on API fail.
 * Law 3 — No Real-Time: no WebSockets/polling — all events are user-triggered.
 *
 * Offline: shows cached tasks with OfflineBanner. Upload/Done require internet.
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  FlatList,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import client, { tokenStorage, authEvents } from '../api/client';
import { offlineCache, CachedTask } from '../cache/offlineCache';
import TaskCard from '../components/TaskCard';
import OfflineBanner from '../components/OfflineBanner';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'Dashboard'> };

export default function DashboardScreen({ navigation }: Props) {
  const [tasks, setTasks] = useState<CachedTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [role, setRole] = useState<string>('');

  // Read role once on mount — determines header title for N1/N2 verification
  useEffect(() => {
    AsyncStorage.getItem('role').then((r) => setRole(r ?? ''));
  }, []);

  // Law 1 — Pull on Focus: always fetch fresh data when screen comes to foreground
  useFocusEffect(
    useCallback(() => {
      fetchTasks();
    }, [])
  );

  const fetchTasks = async () => {
    setLoading(true);
    try {
      // Field names match openapi.yaml FollowUpTask schema
      const response = await client.get('/api/v1/tasks');
      const fetched: CachedTask[] = response.data;
      setTasks(fetched);
      setIsOffline(false);
      await offlineCache.saveTasks(fetched); // update cache for offline use
    } catch (error: any) {
      if (!error.response) {
        // Network error — load from cache
        setIsOffline(true);
        const cached = await offlineCache.getTasks();
        setTasks(cached);
      }
    } finally {
      setLoading(false);
    }
  };

  // Law 2 — Optimistic Update with Rollback
  const handleMarkDone = async (taskId: number) => {
    const previousTasks = [...tasks];

    // Immediate UI update
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: 'Done' as const } : t))
    );

    try {
      // Field names match openapi.yaml TaskUpdateRequest
      await client.patch(`/api/v1/tasks/${taskId}`, { status: 'Done' });
    } catch {
      // Rollback on failure
      setTasks(previousTasks);
      Alert.alert('Sync Failed', 'Task not saved. Please retry.');
    }
  };

  const handleLogout = async () => {
    await tokenStorage.clearTokens();
    await AsyncStorage.multiRemove(['staff_id', 'role']);
    authEvents.emit('logout');
  };

  const pendingTasks = tasks.filter((t) => t.status === 'Pending');

  return (
    <View style={styles.container}>
      <OfflineBanner />

      <View style={styles.header}>
        <Text style={styles.title}>
          {role === 'store_manager' ? 'Store Dashboard' : 'My Tasks'}
        </Text>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.uploadButton}
            onPress={() => navigation.navigate('Upload')}
          >
            <Text style={styles.uploadText}>Upload SAP</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Text style={styles.logoutText}>Logout</Text>
          </TouchableOpacity>
        </View>
      </View>

      {loading && tasks.length === 0 ? (
        <ActivityIndicator color="#6366f1" style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={pendingTasks}
          keyExtractor={(item) => String(item.id)}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={fetchTasks} tintColor="#6366f1" />
          }
          renderItem={({ item }) => (
            <TaskCard
              id={item.id}
              customer_id={item.customer_id}
              task_type={item.task_type}
              due_date={item.due_date}
              status={item.status}
              onPress={(id) => navigation.navigate('TaskDetail', { taskId: id })}
            />
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>No pending tasks. Well done!</Text>
          }
          contentContainerStyle={styles.list}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 56,
  },
  title: { fontSize: 24, fontWeight: '800', color: '#f1f5f9' },
  headerActions: { flexDirection: 'row', gap: 10 },
  uploadButton: {
    backgroundColor: '#334155',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  uploadText: { color: '#f1f5f9', fontSize: 13, fontWeight: '600' },
  logoutButton: {
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  logoutText: { color: '#94a3b8', fontSize: 13, fontWeight: '600' },
  list: { padding: 16, paddingTop: 0 },
  empty: { color: '#64748b', textAlign: 'center', marginTop: 60, fontSize: 16 },
});
