/**
 * UploadScreen — SAP file upload.
 * SRS §5 FR-01: CSV or Excel export from SAP.
 * SRS §15: unmapped column → clear error. No matching Sales Rep → clear error.
 * Requires internet — blocked if offline (SRS §7 NFR-05).
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import * as DocumentPicker from 'react-native-document-picker';
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

export default function UploadScreen({ navigation }: Props) {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);

  const pickAndUpload = async () => {
    let file: any;
    try {
      const picked = await DocumentPicker.pickSingle({
        type: [DocumentPicker.types.csv, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
      });
      file = picked;
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Could not open file picker.');
      }
      return;
    }

    setUploading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        type: file.type ?? 'text/csv',
        name: file.name ?? 'upload.csv',
      } as any);

      const response = await client.post('/api/v1/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setResult(response.data);
    } catch (error: any) {
      const detail = error.response?.data?.detail;

      if (typeof detail === 'object') {
        // SRS §15 structured error responses
        Alert.alert('Upload Failed', detail.message ?? 'Unknown error.');
      } else if (!error.response) {
        // SRS §15: offline — block action
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

  return (
    <ScrollView style={styles.container}>
      <OfflineBanner />

      <TouchableOpacity style={styles.back} onPress={() => navigation.goBack()}>
        <Text style={styles.backText}>← Back</Text>
      </TouchableOpacity>

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
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  back: { padding: 20, paddingTop: 56 },
  backText: { color: '#6366f1', fontSize: 16 },
  title: { fontSize: 24, fontWeight: '800', color: '#f1f5f9', paddingHorizontal: 20 },
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
});
