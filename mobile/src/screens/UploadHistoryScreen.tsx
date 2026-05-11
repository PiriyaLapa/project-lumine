/**
 * UploadHistoryScreen — upload log for this store.
 * Manager-only: GET /api/v1/upload/history (403 shown as error state).
 * Law 1 — Pull on Focus: fetch fresh on every foreground event.
 * Field names match openapi.yaml UploadLog schema exactly.
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
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import { UploadLog } from '../mock/mockData';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'UploadHistory'> };

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function UploadLogCard({ item }: { item: UploadLog }) {
  const isSuccess = item.status === 'success';
  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.filename} numberOfLines={1}>{item.filename}</Text>
        <View style={[styles.badge, isSuccess ? styles.badgeSuccess : styles.badgeError]}>
          <Text style={[styles.badgeText, isSuccess ? styles.badgeTextSuccess : styles.badgeTextError]}>
            {isSuccess ? 'Success' : 'Error'}
          </Text>
        </View>
      </View>
      <Text style={styles.dateRange}>
        {item.date_range_start} → {item.date_range_end}
      </Text>
      <View style={styles.cardFooter}>
        <Text style={styles.meta}>
          Tasks: {item.tasks_created} · Rows: {item.row_count}
        </Text>
        <Text style={styles.uploadedAt}>{formatDate(item.uploaded_at)}</Text>
      </View>
    </View>
  );
}

export default function UploadHistoryScreen({ navigation }: Props) {
  const [logs, setLogs] = useState<UploadLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await client.get('/api/v1/upload/history');
      setLogs(response.data as UploadLog[]);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } };
      if (axiosErr.response?.status === 403) {
        setError('Manager access required to view upload history.');
      } else if (!axiosErr.response) {
        setError('No internet connection. Please try again.');
      } else {
        setError('Failed to load upload history. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Law 1 — Pull on Focus
  useFocusEffect(
    useCallback(() => {
      fetchHistory();
    }, [])
  );

  const renderContent = () => {
    if (loading) {
      return <ActivityIndicator color="#6366f1" style={styles.centered} />;
    }
    if (error) {
      return (
        <View style={styles.centeredContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchHistory}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return (
      <FlatList
        data={logs}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <UploadLogCard item={item} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.empty}>No uploads yet.</Text>
        }
      />
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.title}>Upload History</Text>
      <Text style={styles.subtitle}>SAP files uploaded by your store</Text>

      {renderContent()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 56,
    paddingBottom: 4,
  },
  backText: { color: '#6366f1', fontSize: 16 },
  title: { fontSize: 24, fontWeight: '800', color: '#f1f5f9', paddingHorizontal: 20, marginTop: 12 },
  subtitle: { color: '#64748b', paddingHorizontal: 20, marginTop: 6, marginBottom: 20, fontSize: 14 },

  list: { padding: 16, paddingTop: 0 },

  card: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  filename: {
    color: '#f1f5f9',
    fontWeight: '700',
    fontSize: 15,
    flex: 1,
    marginRight: 10,
  },
  badge: {
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  badgeSuccess: { backgroundColor: '#14532d' },
  badgeError: { backgroundColor: '#450a0a' },
  badgeText: { fontSize: 12, fontWeight: '600' },
  badgeTextSuccess: { color: '#22c55e' },
  badgeTextError: { color: '#ef4444' },

  dateRange: { color: '#94a3b8', fontSize: 13, marginBottom: 8 },

  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  meta: { color: '#64748b', fontSize: 13 },
  uploadedAt: { color: '#64748b', fontSize: 12 },

  centered: { marginTop: 60 },
  centeredContainer: { alignItems: 'center', marginTop: 60, paddingHorizontal: 20 },
  errorText: { color: '#ef4444', fontSize: 14, textAlign: 'center', marginBottom: 16 },
  retryButton: {
    backgroundColor: '#334155',
    borderRadius: 8,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  retryText: { color: '#f1f5f9', fontSize: 14, fontWeight: '600' },
  empty: { color: '#64748b', textAlign: 'center', marginTop: 60, fontSize: 16 },
});
