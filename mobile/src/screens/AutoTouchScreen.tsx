/**
 * AutoTouchScreen — today's Auto-Touch follow-up queue.
 * Data source: GET /api/v1/auto-touch/today. Field names match openapi.yaml
 * AutoTouchCustomer schema exactly.
 *
 * Law 1 — Pull on Focus: fetch fresh queue on every foreground event.
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
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import AutoTouchCard from '../components/AutoTouchCard';
import { THEME } from '../styles/theme';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'AutoTouch'> };

// Field names match openapi.yaml AutoTouchCustomer schema — do not rename
export interface AutoTouchCustomer {
  customer_id: string;     // LOCKED
  customer_name: string;
  language: 'th' | 'en';
  task_id: number;         // LOCKED
  task_type: '2D' | '2W' | '2M';
  due_date: string;
  days_since_purchase: number;
  products: { product_raw: string; product_clean: string; price: number | null; returned: boolean }[];
  channels_available: { line: boolean; email: boolean };
  send_status: string; // LOCKED
}

export default function AutoTouchScreen({ navigation }: Props) {
  const [customers, setCustomers] = useState<AutoTouchCustomer[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      fetchToday();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])
  );

  const fetchToday = async () => {
    setLoading(true);
    try {
      const response = await client.get('/api/v1/auto-touch/today');
      setCustomers(response.data);
      setLoadError(null);
    } catch (error: any) {
      if (!error.response) {
        // Network error — nothing to fall back to for this screen
        setCustomers([]);
      } else {
        // Server responded with an error — surface it, don't silently show empty state
        setLoadError('Could not load today’s follow-ups. Pull down to try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Auto-Touch</Text>
      </View>

      {loading && customers.length === 0 ? (
        <ActivityIndicator color={THEME.colors.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={customers}
          keyExtractor={(item) => String(item.task_id)}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={fetchToday} tintColor={THEME.colors.primary} />
          }
          renderItem={({ item }) => (
            <AutoTouchCard
              task_id={item.task_id}
              customer_id={item.customer_id}
              customer_name={item.customer_name}
              task_type={item.task_type}
              due_date={item.due_date}
              days_since_purchase={item.days_since_purchase}
              products={item.products}
              channels_available={item.channels_available}
              onPress={(taskId, customerId) =>
                navigation.navigate('AutoTouchDetail', { taskId, customer_id: customerId })
              }
              onCustomerPress={(customerId, customerName) =>
                navigation.navigate('CustomerProfile', { customer_id: customerId, customer_name: customerName })
              }
            />
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>
              {loadError ?? 'All caught up — no follow-ups due today.'}
            </Text>
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
    paddingHorizontal: THEME.spacing.lg,
    paddingTop: 56,
    paddingBottom: THEME.spacing.md,
  },
  backBtn: { paddingVertical: 4 },
  backText: { color: THEME.colors.primary, fontSize: THEME.fontSize.md, fontWeight: '600' },
  title: { fontSize: THEME.fontSize.xxl, fontWeight: '800', color: THEME.colors.text },
  list: { padding: THEME.spacing.md, paddingTop: 0 },
  empty: { color: THEME.colors.textMuted, textAlign: 'center', marginTop: 60, fontSize: THEME.fontSize.lg },
});
