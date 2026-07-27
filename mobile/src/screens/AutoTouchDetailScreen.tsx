/**
 * AutoTouchDetailScreen — draft, edit, and act on a single Auto-Touch follow-up.
 *
 * No single-item GET exists — fetches GET /api/v1/auto-touch/today and finds
 * the row by task_id, same convention as TaskDetailScreen against /tasks.
 *
 * Scope: draft + edit + Copy/Share only. AUTO_TOUCH_SEND_ENABLED is off
 * (automated sending needs company authorization not yet granted), so this
 * screen never calls POST /auto-touch/send. "Mark as Contacted" closes the
 * loop via the generic PATCH /api/v1/tasks/{id} endpoint instead — the same
 * one DashboardScreen already uses to mark a task Done.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Share,
} from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import { THEME } from '../styles/theme';
import type { AutoTouchCustomer } from './AutoTouchScreen';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'AutoTouchDetail'>;
  route: RouteProp<RootStackParamList, 'AutoTouchDetail'>;
};

const TASK_TYPE_LABELS: Record<string, string> = {
  '2D': 'Experience Check (T+2)',
  '2W': 'Relationship Building (T+14)',
  '2M': 'Retention Check (T+60)',
};

export default function AutoTouchDetailScreen({ navigation, route }: Props) {
  const { taskId, customer_id } = route.params;

  const [customer, setCustomer] = useState<AutoTouchCustomer | null>(null);
  const [loadingRow, setLoadingRow] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [draftText, setDraftText] = useState('');
  const [originalDraftText, setOriginalDraftText] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const [skipping, setSkipping] = useState(false);
  const [marking, setMarking] = useState(false);

  useEffect(() => {
    fetchRow();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  const fetchRow = async () => {
    setLoadingRow(true);
    try {
      const response = await client.get('/api/v1/auto-touch/today');
      const found: AutoTouchCustomer | undefined = response.data.find(
        (c: AutoTouchCustomer) => c.task_id === taskId
      );
      if (found) {
        setCustomer(found);
        generateMessage(found);
      } else {
        setNotFound(true);
      }
    } catch {
      setNotFound(true);
    } finally {
      setLoadingRow(false);
    }
  };

  const generateMessage = async (target?: AutoTouchCustomer) => {
    const c = target ?? customer;
    if (!c) return;
    setGenerating(true);
    setGenerateError(null);
    try {
      const resp = await client.post('/api/v1/auto-touch/generate-message', {
        customer_id: c.customer_id,
        task_id: c.task_id,
      });
      setDraftText(resp.data.message_text);
      setOriginalDraftText(resp.data.message_text);
    } catch {
      setGenerateError('Could not generate a draft. Tap Regenerate to try again.');
    } finally {
      setGenerating(false);
    }
  };

  const handleRegenerate = () => {
    const isEdited = draftText !== originalDraftText;
    if (isEdited) {
      Alert.alert(
        'Discard your edits?',
        'Regenerating will replace your edited message with a new draft.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Regenerate', style: 'destructive', onPress: () => generateMessage() },
        ]
      );
    } else {
      generateMessage();
    }
  };

  const handleCopy = async () => {
    if (!draftText.trim()) return;
    await Clipboard.setStringAsync(draftText);
    Alert.alert('Copied', 'Message copied to clipboard.');
  };

  const handleShare = async () => {
    if (!draftText.trim()) return;
    try {
      await Share.share({ message: draftText });
    } catch {
      Alert.alert('Share Failed', 'Something went wrong. Please try again.');
    }
  };

  const handleSkip = () => {
    Alert.alert('Skip this follow-up?', 'It will reappear tomorrow.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Skip', style: 'destructive', onPress: doSkip },
    ]);
  };

  const doSkip = async () => {
    setSkipping(true);
    try {
      await client.post(`/api/v1/auto-touch/skip/${customer_id}`);
      navigation.goBack();
    } catch {
      Alert.alert('Skip Failed', 'Please try again.');
    } finally {
      setSkipping(false);
    }
  };

  const handleMarkContacted = () => {
    Alert.alert('Mark as contacted?', 'This marks today’s follow-up as done.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Mark as Contacted', onPress: doMarkContacted },
    ]);
  };

  const doMarkContacted = async () => {
    setMarking(true);
    try {
      await client.patch(`/api/v1/tasks/${taskId}`, { status: 'Done' });
      navigation.goBack();
    } catch {
      Alert.alert('Sync Failed', 'Task not saved. Please retry.');
    } finally {
      setMarking(false);
    }
  };

  if (loadingRow) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={THEME.colors.primary} size="large" />
      </View>
    );
  }

  if (notFound || !customer) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Auto-Touch</Text>
        </View>
        <View style={styles.centered}>
          <Text style={styles.emptyText}>This follow-up is no longer due.</Text>
        </View>
      </View>
    );
  }

  const hasNoChannel = !customer.channels_available.line && !customer.channels_available.email;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Auto-Touch</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.card}>
          <Text style={styles.customerName}>{customer.customer_name}</Text>
          <Text style={styles.field}>
            {TASK_TYPE_LABELS[customer.task_type]}
            <Text style={styles.langChip}>  {customer.language.toUpperCase()}</Text>
          </Text>
          <Text style={styles.field}>Due: <Text style={styles.value}>{customer.due_date}</Text></Text>
          <Text style={styles.field}>
            Days since purchase: <Text style={styles.value}>{customer.days_since_purchase}</Text>
          </Text>
          {customer.products.length > 0 && (
            <Text style={styles.field}>
              Products: <Text style={styles.value}>
                {customer.products.map((p) => p.product_clean).join(', ')}
              </Text>
            </Text>
          )}
          {hasNoChannel && (
            <Text style={styles.warningNote}>
              No LINE or email on file for this customer — you'll need another way to reach them.
            </Text>
          )}
        </View>

        <Text style={styles.label}>Message Draft</Text>
        {generating && draftText === '' ? (
          <View style={styles.draftLoading}>
            <ActivityIndicator color={THEME.colors.primary} />
            <Text style={styles.draftLoadingText}>Drafting message…</Text>
          </View>
        ) : (
          <TextInput
            style={styles.draftInput}
            value={draftText}
            onChangeText={setDraftText}
            multiline
            numberOfLines={6}
            placeholder="Draft will appear here…"
            placeholderTextColor={THEME.colors.textMuted}
            textAlignVertical="top"
          />
        )}
        {generateError && <Text style={styles.errorText}>{generateError}</Text>}

        <TouchableOpacity
          style={styles.outlineButton}
          onPress={handleRegenerate}
          disabled={generating}
        >
          <Text style={styles.outlineButtonText}>
            {generating ? 'Generating…' : 'Regenerate'}
          </Text>
        </TouchableOpacity>

        <View style={styles.row}>
          <TouchableOpacity
            style={[styles.outlineButton, styles.rowButton]}
            onPress={handleCopy}
            disabled={!draftText.trim()}
          >
            <Text style={styles.outlineButtonText}>Copy</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.outlineButton, styles.rowButton]}
            onPress={handleShare}
            disabled={!draftText.trim()}
          >
            <Text style={styles.outlineButtonText}>Share</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.divider} />

        <TouchableOpacity
          style={styles.primaryButton}
          onPress={handleMarkContacted}
          disabled={marking}
        >
          <Text style={styles.primaryButtonText}>
            {marking ? 'Saving…' : '✓ Mark as Contacted'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.skipButton} onPress={handleSkip} disabled={skipping}>
          <Text style={styles.skipButtonText}>
            {skipping ? 'Skipping…' : 'Skip — remind me tomorrow'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.colors.background },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: THEME.colors.background },
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
  scroll: { padding: THEME.spacing.lg, paddingBottom: 40 },
  card: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.md,
    padding: THEME.spacing.lg,
    marginBottom: THEME.spacing.lg,
    shadowColor: THEME.colors.primaryShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  customerName: { fontSize: THEME.fontSize.xl, fontWeight: '700', color: THEME.colors.text, marginBottom: THEME.spacing.sm },
  field: { color: THEME.colors.textSecondary, fontSize: THEME.fontSize.sm, marginBottom: 8 },
  value: { color: THEME.colors.text, fontWeight: '600' },
  langChip: { color: THEME.colors.textMuted, fontSize: THEME.fontSize.xs, fontWeight: '700' },
  warningNote: {
    color: THEME.colors.warning,
    fontSize: THEME.fontSize.sm,
    marginTop: 4,
  },
  label: {
    fontSize: THEME.fontSize.sm,
    fontWeight: '600',
    color: THEME.colors.textSecondary,
    marginBottom: THEME.spacing.xs,
  },
  draftLoading: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.md,
    padding: THEME.spacing.lg,
    minHeight: 120,
    alignItems: 'center',
    justifyContent: 'center',
    gap: THEME.spacing.sm,
  },
  draftLoadingText: { color: THEME.colors.textMuted, fontSize: THEME.fontSize.sm },
  draftInput: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.md,
    padding: THEME.spacing.md,
    fontSize: THEME.fontSize.md,
    color: THEME.colors.text,
    borderWidth: 1,
    borderColor: THEME.colors.divider,
    minHeight: 120,
    marginBottom: THEME.spacing.sm,
  },
  errorText: {
    color: THEME.colors.error,
    fontSize: THEME.fontSize.sm,
    marginBottom: THEME.spacing.sm,
  },
  outlineButton: {
    borderRadius: THEME.radius.md,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: THEME.colors.primary,
    backgroundColor: 'transparent',
    marginTop: THEME.spacing.sm,
  },
  outlineButtonText: { color: THEME.colors.primary, fontSize: THEME.fontSize.lg, fontWeight: '700' },
  row: { flexDirection: 'row', gap: THEME.spacing.sm },
  rowButton: { flex: 1 },
  divider: {
    height: 1,
    backgroundColor: THEME.colors.divider,
    marginVertical: THEME.spacing.lg,
  },
  primaryButton: {
    backgroundColor: THEME.colors.primary,
    borderRadius: THEME.radius.md,
    padding: 16,
    alignItems: 'center',
  },
  primaryButtonText: { color: THEME.colors.card, fontSize: THEME.fontSize.lg, fontWeight: '700' },
  skipButton: {
    borderRadius: THEME.radius.md,
    padding: 14,
    alignItems: 'center',
    marginTop: THEME.spacing.sm,
  },
  skipButtonText: { color: THEME.colors.textSecondary, fontSize: THEME.fontSize.md, fontWeight: '600' },
  emptyText: { color: THEME.colors.textMuted, fontSize: THEME.fontSize.md, textAlign: 'center' },
});
