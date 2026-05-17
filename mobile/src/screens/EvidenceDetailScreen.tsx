/**
 * EvidenceDetailScreen — view and edit evidence for a completed task.
 * Loads: GET /api/v1/evidence/{taskId}
 * Saves: PATCH /api/v1/evidence/{evidenceId}
 *
 * Rules:
 * - notes omitted → keep existing notes (no overwrite)
 * - image not changed → keep existing Drive photo (no delete)
 * - Save button disabled until notes or photo changes
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import { THEME } from '../styles/theme';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'EvidenceDetail'>;
  route: RouteProp<RootStackParamList, 'EvidenceDetail'>;
};

interface EvidenceData {
  id: number;
  task_id: number;
  notes: string | null;
  image_uri: string | null;
  image_size_kb: number | null;
  timestamp: string | null;
}

export default function EvidenceDetailScreen({ navigation, route }: Props) {
  const { taskId } = route.params;

  const [evidence, setEvidence] = useState<EvidenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState('');

  // Edit state
  const [editedNotes, setEditedNotes] = useState('');
  const [newImageUri, setNewImageUri] = useState<string | null>(null);

  useEffect(() => {
    fetchEvidence();
  }, [taskId]);

  const fetchEvidence = async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await client.get(`/api/v1/evidence/${taskId}`);
      const data: EvidenceData = resp.data;
      setEvidence(data);
      setEditedNotes(data.notes ?? '');
    } catch (err: any) {
      if (err.response?.status === 404) {
        setNotFound(true);
      } else {
        setError('Failed to load evidence. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const isDirty =
    evidence !== null &&
    (editedNotes !== (evidence.notes ?? '') || newImageUri !== null);

  const handlePickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission required', 'Allow access to your photo library to update evidence.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.7,
    });
    if (!result.canceled && result.assets.length > 0) {
      setNewImageUri(result.assets[0].uri);
    }
  };

  const handleSave = async () => {
    if (!evidence || !isDirty) return;
    setSaving(true);
    setError('');

    const formData = new FormData();

    if (editedNotes !== (evidence.notes ?? '')) {
      formData.append('notes', editedNotes);
    }

    if (newImageUri) {
      formData.append('image', {
        uri: newImageUri,
        type: 'image/jpeg',
        name: 'evidence.jpg',
      } as any);
    }

    try {
      const resp = await client.patch(`/api/v1/evidence/${evidence.id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const updated: EvidenceData = resp.data;
      setEvidence(updated);
      setEditedNotes(updated.notes ?? '');
      setNewImageUri(null);
    } catch (err: any) {
      if (err.response?.status === 413) {
        setError('Image too large. Please choose a smaller photo.');
      } else if (err.response?.status === 403) {
        setError('You do not have permission to edit this evidence.');
      } else {
        setError('Save failed. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Render states
  // ---------------------------------------------------------------------------

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={THEME.colors.primary} size="large" />
      </View>
    );
  }

  if (notFound) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Evidence</Text>
        </View>
        <View style={styles.centered}>
          <Text style={styles.emptyText}>No evidence logged for this task yet.</Text>
        </View>
      </View>
    );
  }

  const displayImageUri = newImageUri ?? evidence?.image_uri ?? null;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Evidence</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

        {/* Notes */}
        <Text style={styles.label}>Notes</Text>
        <TextInput
          style={styles.notesInput}
          value={editedNotes}
          onChangeText={setEditedNotes}
          multiline
          numberOfLines={5}
          placeholder="Add notes about this follow-up…"
          placeholderTextColor={THEME.colors.textMuted}
          textAlignVertical="top"
        />

        {/* Photo */}
        <Text style={styles.label}>Photo</Text>
        {displayImageUri ? (
          <View style={styles.imageWrapper}>
            <Image
              source={{ uri: displayImageUri }}
              style={styles.evidenceImage}
              resizeMode="cover"
            />
            {newImageUri && (
              <Text style={styles.newPhotoLabel}>New photo selected</Text>
            )}
          </View>
        ) : (
          <View style={styles.noPhoto}>
            <Text style={styles.noPhotoText}>No photo attached</Text>
          </View>
        )}

        <TouchableOpacity style={styles.photoBtn} onPress={handlePickImage}>
          <Text style={styles.photoBtnText}>
            {displayImageUri ? 'Change Photo' : 'Add Photo'}
          </Text>
        </TouchableOpacity>

        {evidence?.timestamp && (
          <Text style={styles.timestamp}>
            Logged: {new Date(evidence.timestamp).toLocaleString()}
          </Text>
        )}

        {error !== '' && <Text style={styles.errorText}>{error}</Text>}

        <TouchableOpacity
          style={[styles.saveBtn, (!isDirty || saving) && styles.saveBtnDisabled]}
          onPress={handleSave}
          disabled={!isDirty || saving}
        >
          <Text style={styles.saveBtnText}>
            {saving ? 'Saving…' : 'Save Changes'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.colors.background },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
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
  title: { fontSize: THEME.fontSize.xl, fontWeight: '800', color: THEME.colors.text },
  scroll: { padding: THEME.spacing.lg, paddingBottom: 40 },
  label: {
    fontSize: THEME.fontSize.sm,
    fontWeight: '600',
    color: THEME.colors.textSecondary,
    marginBottom: THEME.spacing.xs,
    marginTop: THEME.spacing.md,
  },
  notesInput: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.md,
    padding: THEME.spacing.md,
    fontSize: THEME.fontSize.md,
    color: THEME.colors.text,
    borderWidth: 1,
    borderColor: THEME.colors.divider,
    minHeight: 120,
  },
  imageWrapper: { borderRadius: THEME.radius.md, overflow: 'hidden', marginBottom: THEME.spacing.sm },
  evidenceImage: { width: '100%', height: 220, borderRadius: THEME.radius.md },
  newPhotoLabel: {
    fontSize: THEME.fontSize.xs,
    color: THEME.colors.primary,
    fontWeight: '600',
    marginTop: THEME.spacing.xs,
  },
  noPhoto: {
    backgroundColor: THEME.colors.surface,
    borderRadius: THEME.radius.md,
    height: 100,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: THEME.spacing.sm,
  },
  noPhotoText: { color: THEME.colors.textMuted, fontSize: THEME.fontSize.sm },
  photoBtn: {
    borderWidth: 1,
    borderColor: THEME.colors.primary,
    borderRadius: THEME.radius.md,
    paddingVertical: 10,
    alignItems: 'center',
    marginBottom: THEME.spacing.md,
  },
  photoBtnText: { color: THEME.colors.primary, fontSize: THEME.fontSize.md, fontWeight: '600' },
  timestamp: {
    fontSize: THEME.fontSize.xs,
    color: THEME.colors.textMuted,
    marginBottom: THEME.spacing.md,
    textAlign: 'center',
  },
  errorText: {
    color: THEME.colors.error,
    fontSize: THEME.fontSize.sm,
    marginBottom: THEME.spacing.md,
    textAlign: 'center',
  },
  saveBtn: {
    backgroundColor: THEME.colors.primary,
    borderRadius: THEME.radius.pill,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: THEME.spacing.sm,
  },
  saveBtnDisabled: { opacity: 0.4 },
  saveBtnText: { color: THEME.colors.card, fontSize: THEME.fontSize.lg, fontWeight: '700' },
  emptyText: { color: THEME.colors.textMuted, fontSize: THEME.fontSize.md, textAlign: 'center' },
});
