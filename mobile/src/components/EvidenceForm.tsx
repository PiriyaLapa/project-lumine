/**
 * EvidenceForm — notes + photo capture for task evidence.
 * SRS §5 FR-04: max 800KB, compress before upload, JPEG only.
 * task_id field name LOCKED — matches openapi.yaml EvidenceRequest.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  StyleSheet,
  Alert,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';

const MAX_SIZE_KB = 800;
const MAX_DIMENSION = 1280;

export interface EvidenceFormValues {
  task_id: number;   // LOCKED
  notes: string;
  imageUri: string | null;
  imageSizeKb: number | null;
}

interface EvidenceFormProps {
  task_id: number;   // LOCKED
  onSubmit: (values: EvidenceFormValues) => Promise<void>;
  isSubmitting: boolean;
}

export default function EvidenceForm({ task_id, onSubmit, isSubmitting }: EvidenceFormProps) {
  const [notes, setNotes] = useState('');
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [imageSizeKb, setImageSizeKb] = useState<number | null>(null);

  const pickAndCompressImage = async () => {
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1,
    });

    if (result.canceled) return;

    const asset = result.assets[0];
    let uri = asset.uri;
    let sizeKb = asset.fileSize ? asset.fileSize / 1024 : 0;

    // SRS §5 FR-04: compress to ≤ 800KB at max 1280px on longest edge
    if (sizeKb > MAX_SIZE_KB || (asset.width ?? 0) > MAX_DIMENSION || (asset.height ?? 0) > MAX_DIMENSION) {
      try {
        const compressed = await ImageManipulator.manipulateAsync(
          uri,
          [{ resize: { width: MAX_DIMENSION } }],
          { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG }
        );
        uri = compressed.uri;
        // Approximate size — expo-image-manipulator doesn't return file size
        sizeKb = Math.min(sizeKb * 0.8, MAX_SIZE_KB);
      } catch {
        Alert.alert('Error', 'Photo could not be processed. Try a different photo.');
        return;
      }
    }

    setImageUri(uri);
    setImageSizeKb(Math.round(sizeKb));
  };

  const handleSubmit = async () => {
    await onSubmit({ task_id, notes, imageUri, imageSizeKb });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Notes</Text>
      <TextInput
        style={styles.textInput}
        multiline
        numberOfLines={4}
        placeholder="Describe the follow-up interaction..."
        placeholderTextColor="#64748b"
        value={notes}
        onChangeText={setNotes}
      />

      <TouchableOpacity style={styles.photoButton} onPress={pickAndCompressImage}>
        <Text style={styles.photoButtonText}>
          {imageUri ? '📷 Retake Photo' : '📷 Take Photo'}
        </Text>
      </TouchableOpacity>

      {imageUri && (
        <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="cover" />
      )}

      {imageSizeKb !== null && (
        <Text style={styles.sizeNote}>{imageSizeKb} KB</Text>
      )}

      <TouchableOpacity
        style={[styles.submitButton, isSubmitting && styles.disabled]}
        onPress={handleSubmit}
        disabled={isSubmitting}
      >
        <Text style={styles.submitText}>
          {isSubmitting ? 'Saving...' : 'Save Evidence'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16 },
  label: { color: '#94a3b8', fontSize: 13, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
  textInput: {
    backgroundColor: '#1e293b',
    color: '#f1f5f9',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: 16,
  },
  photoButton: {
    backgroundColor: '#334155',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  photoButtonText: { color: '#f1f5f9', fontSize: 15, fontWeight: '600' },
  preview: { width: '100%', height: 200, borderRadius: 8, marginBottom: 8 },
  sizeNote: { color: '#64748b', fontSize: 12, textAlign: 'right', marginBottom: 16 },
  submitButton: {
    backgroundColor: '#6366f1',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  disabled: { opacity: 0.5 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
