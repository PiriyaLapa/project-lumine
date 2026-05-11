/**
 * UploadScreen — SAP file upload.
 * SRS §5 FR-01: CSV or Excel export from SAP.
 * SRS §15: unmapped column → clear error. No matching Sales Rep → clear error.
 * Requires internet — blocked if offline (SRS §7 NFR-05).
 *
 * 409 ConflictResponse: shows modal with overlapping upload details.
 * Manager role: shows "History" header button → UploadHistoryScreen.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  ActivityIndicator,
  Modal,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import OfflineBanner from '../components/OfflineBanner';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'Upload'> };

interface UploadResult {
  tasks_created: number;       // LOCKED — openapi.yaml UploadResponse
  customers_processed: number; // LOCKED
  cycles_reset: number;        // LOCKED
  errors: string[];            // LOCKED
}

interface OverlappingUpload {
  filename: string;
  uploaded_at: string;
  date_range: string;
}

interface ConflictDetail {
  conflict: boolean;
  overlapping_upload: OverlappingUpload;
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function UploadScreen({ navigation }: Props) {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [role, setRole] = useState('');
  const [conflictDetail, setConflictDetail] = useState<ConflictDetail | null>(null);
  const pendingFileRef = useRef<DocumentPicker.DocumentPickerAsset | null>(null);

  useEffect(() => {
    AsyncStorage.getItem('role').then((r) => setRole(r ?? ''));
  }, []);

  const doUpload = async (asset: DocumentPicker.DocumentPickerAsset, force: boolean) => {
    setUploading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', {
        uri: asset.uri,
        type: asset.mimeType ?? 'text/csv',
        name: asset.name ?? 'upload.csv',
      } as unknown as Blob);

      const url = force ? '/api/v1/upload?force=true' : '/api/v1/upload';
      const response = await client.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setResult(response.data as UploadResult);
      setConflictDetail(null);
      pendingFileRef.current = null;
    } catch (error: unknown) {
      const axiosErr = error as { response?: { status?: number; data?: unknown } };
      const status = axiosErr.response?.status;
      const data = axiosErr.response?.data;

      if (status === 409 && data && typeof data === 'object' && 'conflict' in data) {
        pendingFileRef.current = asset;
        setConflictDetail(data as ConflictDetail);
      } else if (status !== undefined && typeof data === 'object' && data !== null && 'detail' in data) {
        const detail = (data as { detail: unknown }).detail;
        if (typeof detail === 'object' && detail !== null && 'message' in detail) {
          Alert.alert('Upload Failed', (detail as { message: string }).message);
        } else {
          Alert.alert('Upload Failed', 'Please try again.');
        }
      } else if (!axiosErr.response) {
        Alert.alert(
          'No Internet',
          "You're offline. SAP upload requires internet connection."
        );
      } else {
        Alert.alert('Upload Failed', 'Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  const pickAndUpload = async () => {
    const picked = await DocumentPicker.getDocumentAsync({
      type: ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
      copyToCacheDirectory: true,
    });

    if (picked.canceled) return;
    await doUpload(picked.assets[0], false);
  };

  const handleForceUpload = async () => {
    if (!pendingFileRef.current) return;
    setConflictDetail(null);
    await doUpload(pendingFileRef.current, true);
  };

  return (
    <ScrollView style={styles.container}>
      <OfflineBanner />

      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        {role === 'store_manager' && (
          <TouchableOpacity onPress={() => navigation.navigate('UploadHistory')}>
            <Text style={styles.historyText}>History</Text>
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.title}>Upload SAP File</Text>
      <Text style={styles.subtitle}>Select a CSV or Excel export from SAP</Text>

      <TouchableOpacity
        style={[styles.uploadButton, uploading && styles.disabled]}
        onPress={pickAndUpload}
        disabled={uploading}
      >
        {uploading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.uploadText}>Select & Upload File</Text>
        )}
      </TouchableOpacity>

      {result && (
        <View style={styles.resultCard}>
          <Text style={styles.resultTitle}>Upload Complete</Text>
          <Text style={styles.resultRow}>✓ Tasks created: {result.tasks_created}</Text>
          <Text style={styles.resultRow}>✓ Customers processed: {result.customers_processed}</Text>
          {result.cycles_reset > 0 && (
            <Text style={styles.resultRow}>↺ Cycles reset: {result.cycles_reset}</Text>
          )}
          {result.errors.length > 0 && (
            <View style={styles.errorsSection}>
              <Text style={styles.errorsTitle}>
                {result.errors.length} row(s) skipped:
              </Text>
              {result.errors.map((e, i) => (
                <Text key={i} style={styles.errorRow}>• {e}</Text>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Conflict modal — shown on 409 */}
      <Modal
        visible={conflictDetail !== null}
        transparent
        animationType="fade"
        onRequestClose={() => setConflictDetail(null)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Duplicate Date Range</Text>
            <Text style={styles.modalBody}>
              This date range overlaps an existing upload:
            </Text>

            <View style={styles.modalDivider} />

            <View style={styles.modalRow}>
              <Text style={styles.modalLabel}>Filename</Text>
              <Text style={styles.modalValue} numberOfLines={1}>
                {conflictDetail?.overlapping_upload.filename}
              </Text>
            </View>
            <View style={styles.modalRow}>
              <Text style={styles.modalLabel}>Uploaded</Text>
              <Text style={styles.modalValue}>
                {conflictDetail ? formatDateTime(conflictDetail.overlapping_upload.uploaded_at) : ''}
              </Text>
            </View>
            <View style={styles.modalRow}>
              <Text style={styles.modalLabel}>Range</Text>
              <Text style={styles.modalValue}>
                {conflictDetail?.overlapping_upload.date_range}
              </Text>
            </View>

            <View style={styles.modalDivider} />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setConflictDetail(null)}
              >
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.forceButton}
                onPress={handleForceUpload}
                disabled={uploading}
              >
                {uploading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.forceText}>Upload Anyway</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
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
  historyText: { color: '#6366f1', fontSize: 16, fontWeight: '600' },
  title: { fontSize: 24, fontWeight: '800', color: '#f1f5f9', paddingHorizontal: 20, marginTop: 12 },
  subtitle: { color: '#64748b', paddingHorizontal: 20, marginTop: 8, marginBottom: 32, fontSize: 14 },
  uploadButton: {
    backgroundColor: '#6366f1',
    margin: 20,
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    minHeight: 60,
    justifyContent: 'center',
  },
  disabled: { opacity: 0.5 },
  uploadText: { color: '#fff', fontSize: 17, fontWeight: '700' },
  resultCard: { backgroundColor: '#1e293b', margin: 20, borderRadius: 12, padding: 20 },
  resultTitle: { color: '#22c55e', fontSize: 18, fontWeight: '700', marginBottom: 12 },
  resultRow: { color: '#f1f5f9', fontSize: 14, marginBottom: 6 },
  errorsSection: { marginTop: 12, borderTopWidth: 1, borderTopColor: '#334155', paddingTop: 12 },
  errorsTitle: { color: '#f59e0b', fontSize: 13, fontWeight: '600', marginBottom: 6 },
  errorRow: { color: '#94a3b8', fontSize: 13, marginBottom: 4 },

  // Conflict modal
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  modalCard: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 12,
  },
  modalTitle: {
    color: '#f1f5f9',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
  },
  modalBody: {
    color: '#94a3b8',
    fontSize: 14,
    marginBottom: 16,
  },
  modalDivider: {
    height: 1,
    backgroundColor: '#334155',
    marginVertical: 16,
  },
  modalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  modalLabel: {
    color: '#64748b',
    fontSize: 13,
    fontWeight: '600',
    width: 70,
  },
  modalValue: {
    color: '#f1f5f9',
    fontSize: 13,
    flex: 1,
    textAlign: 'right',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 10,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#334155',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  cancelText: {
    color: '#f1f5f9',
    fontSize: 15,
    fontWeight: '600',
  },
  forceButton: {
    flex: 1,
    backgroundColor: '#dc2626',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    minHeight: 48,
    justifyContent: 'center',
  },
  forceText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
});
