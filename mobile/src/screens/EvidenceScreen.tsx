/**
 * EvidenceScreen — notes + photo upload for a task.
 * SRS §5 FR-04: max 800KB, JPEG only, compress on device before send.
 * SRS §15: if Drive upload fails → save with image_uri=null, show retry option.
 * task_id field LOCKED — matches openapi.yaml EvidenceRequest.
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import EvidenceForm, { EvidenceFormValues } from '../components/EvidenceForm';
import OfflineBanner from '../components/OfflineBanner';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Evidence'>;
  route: RouteProp<RootStackParamList, 'Evidence'>;
};

export default function EvidenceScreen({ navigation, route }: Props) {
  const { taskId } = route.params;
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (values: EvidenceFormValues) => {
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      // Field names match openapi.yaml EvidenceRequest — LOCKED
      formData.append('task_id', String(values.task_id));
      formData.append('notes', values.notes);

      if (values.imageUri) {
        formData.append('image', {
          uri: values.imageUri,
          type: 'image/jpeg',
          name: `evidence_${values.task_id}_${Date.now()}.jpg`,
        } as any);
      }

      await client.post('/api/v1/evidence', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      Alert.alert('Saved', 'Evidence logged successfully.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (error: any) {
      const detail = error.response?.data?.detail ?? '';
      if (typeof detail === 'object' && detail.error_code === 'DRIVE_UPLOAD_FAILED') {
        // SRS §15: note saved, photo failed — show retry option
        Alert.alert(
          'Note Saved',
          'Photo upload failed — tap to retry.',
          [
            { text: 'Retry Photo', onPress: () => handleSubmit(values) },
            { text: 'OK', onPress: () => navigation.goBack() },
          ]
        );
      } else {
        Alert.alert('Error', 'Could not save evidence. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <OfflineBanner />

      <View style={styles.header}>
        <Text style={styles.backText} onPress={() => navigation.goBack()}>← Back</Text>
        <Text style={styles.title}>Log Evidence</Text>
      </View>

      <EvidenceForm
        task_id={taskId}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  header: { padding: 20, paddingTop: 56 },
  backText: { color: '#6366f1', fontSize: 16, marginBottom: 12 },
  title: { fontSize: 24, fontWeight: '800', color: '#f1f5f9' },
});
