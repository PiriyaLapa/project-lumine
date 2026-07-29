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

import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  FlatList,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { RootStackParamList } from '../navigation/AppNavigator';
import client, { tokenStorage, authEvents } from '../api/client';
import { offlineCache, CachedTask } from '../cache/offlineCache';
import TaskCard from '../components/TaskCard';
import OfflineBanner from '../components/OfflineBanner';
import AppDrawer from '../components/AppDrawer';
import { THEME } from '../styles/theme';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'Dashboard'> };

export default function DashboardScreen({ navigation }: Props) {
  const [tasks, setTasks] = useState<CachedTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [role, setRole] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [autoTouchDue, setAutoTouchDue] = useState(0);
  const [drawerVisible, setDrawerVisible] = useState(false);

  // useFocusEffect and RefreshControl's onRefresh both call fetchTasks — a ref
  // (not state) guards against them racing, since state updates aren't visible
  // synchronously across two calls firing close together.
  const isFetchingTasksRef = useRef(false);

  // Read role once on mount — determines header title for N1/N2 verification
  useEffect(() => {
    AsyncStorage.getItem('role').then((r) => setRole(r ?? ''));
  }, []);

  // Law 1 — Pull on Focus: always fetch fresh data when screen comes to foreground
  useFocusEffect(
    useCallback(() => {
      fetchTasks();
      fetchAutoTouchStatus();
    }, [])
  );

  const fetchTasks = async () => {
    if (isFetchingTasksRef.current) return;
    isFetchingTasksRef.current = true;
    setLoading(true);
    try {
      // Field names match openapi.yaml FollowUpTask schema
      const response = await client.get('/api/v1/tasks');
      const fetched: CachedTask[] = response.data;
      setTasks(fetched);
      setIsOffline(false);
      setLoadError(null);
      await offlineCache.saveTasks(fetched); // update cache for offline use
    } catch (error: any) {
      if (!error.response) {
        // Network error — load from cache
        setIsOffline(true);
        const cached = await offlineCache.getTasks();
        setTasks(cached);
      } else {
        // Server responded with an error (401/403/500/etc.) — must not fall
        // through silently, since the empty state below reads as "you're
        // all caught up." Surface it explicitly instead of showing a false
        // "No pending tasks. Well done!" for what's actually a failed load.
        setLoadError('Could not load your tasks. Pull down to try again.');
      }
    } finally {
      setLoading(false);
      isFetchingTasksRef.current = false;
    }
  };

  // Decorative badge — a failed fetch must not block or error the main task
  // list, so this silently no-ops to 0 rather than surfacing loadError.
  const fetchAutoTouchStatus = async () => {
    try {
      const response = await client.get('/api/v1/auto-touch/status');
      setAutoTouchDue(response.data.pending);
    } catch {
      setAutoTouchDue(0);
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
  const uniqueStaffNames = [
    ...new Set(pendingTasks.map((t) => t.staff_name).filter((n): n is string => !!n)),
  ];
  const filteredTasks = activeFilter
    ? pendingTasks.filter((t) => t.staff_name === activeFilter)
    : pendingTasks;

  return (
    <View style={styles.container}>
      <OfflineBanner />

      <View style={styles.header}>
        <TouchableOpacity
          style={styles.hamburgerButton}
          onPress={() => setDrawerVisible(true)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Ionicons name="menu" size={26} color={THEME.colors.text} />
          {autoTouchDue > 0 && (
            <View style={styles.hamburgerBadge}>
              <Text style={styles.badgeText}>{autoTouchDue}</Text>
            </View>
          )}
        </TouchableOpacity>
        <Text style={styles.title}>
          {role === 'store_manager' ? 'Store Dashboard' : 'My Tasks'}
        </Text>
      </View>

      <AppDrawer
        visible={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        autoTouchDue={autoTouchDue}
        onLogout={handleLogout}
        navigation={navigation}
      />

      {loading && tasks.length === 0 ? (
        <ActivityIndicator color={THEME.colors.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={filteredTasks}
          keyExtractor={(item) => String(item.id)}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={fetchTasks} tintColor={THEME.colors.primary} />
          }
          ListHeaderComponent={
            role === 'store_manager' && uniqueStaffNames.length > 0 ? (
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                style={styles.chipsScroll}
                contentContainerStyle={styles.chipsContent}
              >
                <TouchableOpacity
                  style={[styles.chip, activeFilter === null && styles.chipActive]}
                  onPress={() => setActiveFilter(null)}
                >
                  <Text style={[styles.chipText, activeFilter === null && styles.chipTextActive]}>
                    All
                  </Text>
                </TouchableOpacity>
                {uniqueStaffNames.map((name) => (
                  <TouchableOpacity
                    key={name}
                    style={[styles.chip, activeFilter === name && styles.chipActive]}
                    onPress={() => setActiveFilter(name)}
                  >
                    <Text style={[styles.chipText, activeFilter === name && styles.chipTextActive]}>
                      {name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            ) : null
          }
          renderItem={({ item }) => (
            <TaskCard
              id={item.id}
              customer_id={item.customer_id}
              customer_name={item.customer_name}
              task_type={item.task_type}
              due_date={item.due_date}
              status={item.status}
              staff_name={item.staff_name}
              onPress={(id) => navigation.navigate('TaskDetail', { taskId: id })}
              onCustomerPress={(customerId, customerName) =>
                navigation.navigate('CustomerProfile', { customer_id: customerId, customer_name: customerName })
              }
            />
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>{loadError ?? 'No pending tasks. Well done!'}</Text>
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
    flexDirection: 'row',
    alignItems: 'center',
    gap: THEME.spacing.md,
    padding: 20,
    paddingTop: 56,
  },
  title: { fontSize: THEME.fontSize.xxl, fontWeight: '800', color: THEME.colors.text },
  hamburgerButton: { position: 'relative', padding: 2 },
  hamburgerBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: THEME.colors.error,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 3,
  },
  badgeText: { color: THEME.colors.card, fontSize: THEME.fontSize.xs, fontWeight: '700' },
  list: { padding: 16, paddingTop: 0 },
  empty: { color: THEME.colors.textMuted, textAlign: 'center', marginTop: 60, fontSize: THEME.fontSize.lg },
  chipsScroll: { marginBottom: 12 },
  chipsContent: { paddingHorizontal: 16, gap: 8 },
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
});
