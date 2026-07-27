/**
 * AutoTouchCard — displays a single AutoTouchCustomer row in the Auto-Touch queue.
 * Field names match openapi.yaml AutoTouchCustomer schema exactly (LOCKED).
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { THEME } from '../styles/theme';

export interface AutoTouchCardProduct {
  product_clean: string;
}

// Field names match openapi.yaml — do not rename
export interface AutoTouchCardProps {
  task_id: number;         // LOCKED
  customer_id: string;     // LOCKED
  customer_name: string;
  task_type: '2D' | '2W' | '2M';
  due_date: string;
  days_since_purchase: number;
  products: AutoTouchCardProduct[];
  channels_available: { line: boolean; email: boolean };
  onPress: (taskId: number, customerId: string) => void;
}

const TASK_TYPE_LABELS: Record<string, string> = {
  '2D': 'Experience Check (T+2)',
  '2W': 'Relationship Building (T+14)',
  '2M': 'Retention Check (T+60)',
};

export default function AutoTouchCard({
  task_id,
  customer_id,
  customer_name,
  task_type,
  due_date,
  days_since_purchase,
  products,
  channels_available,
  onPress,
}: AutoTouchCardProps) {
  const isOverdue = new Date(due_date) < new Date();
  const hasNoChannel = !channels_available.line && !channels_available.email;

  return (
    <TouchableOpacity
      style={[styles.card, isOverdue && styles.overdue]}
      onPress={() => onPress(task_id, customer_id)}
      activeOpacity={0.8}
    >
      <View style={styles.header}>
        <Text style={styles.taskType}>{TASK_TYPE_LABELS[task_type]}</Text>
        <Text style={styles.days}>{days_since_purchase}d since purchase</Text>
      </View>
      <Text style={styles.customerName}>{customer_name}</Text>
      <Text style={styles.customerId}>Customer: {customer_id}</Text>
      {products.length > 0 && (
        <Text style={styles.products} numberOfLines={1}>
          {products.map((p) => p.product_clean).join(', ')}
        </Text>
      )}
      <Text style={[styles.dueDate, isOverdue && styles.overdueText]}>
        Due: {due_date}{isOverdue ? ' — OVERDUE' : ''}
      </Text>

      <View style={styles.channelRow}>
        <View style={[styles.channelDot, channels_available.line ? styles.channelOn : styles.channelOff]} />
        <Text style={styles.channelLabel}>LINE</Text>
        <View style={[styles.channelDot, channels_available.email ? styles.channelOn : styles.channelOff]} />
        <Text style={styles.channelLabel}>Email</Text>
        {hasNoChannel && <Text style={styles.noChannelTag}>No contact channel on file</Text>}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.md,
    padding: THEME.spacing.md,
    marginBottom: THEME.spacing.sm,
    borderLeftWidth: 4,
    borderLeftColor: THEME.colors.divider,
    shadowColor: THEME.colors.primaryShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  overdue: {
    borderLeftColor: THEME.colors.error,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: THEME.spacing.xs,
  },
  taskType: {
    color: THEME.colors.text,
    fontWeight: '600',
    fontSize: THEME.fontSize.sm,
    flex: 1,
  },
  days: {
    color: THEME.colors.textSecondary,
    fontSize: THEME.fontSize.xs,
  },
  customerName: {
    color: THEME.colors.text,
    fontWeight: '700',
    fontSize: THEME.fontSize.md,
    marginBottom: 2,
  },
  customerId: {
    color: THEME.colors.textSecondary,
    fontSize: THEME.fontSize.xs,
    marginBottom: THEME.spacing.xs,
  },
  products: {
    color: THEME.colors.textSecondary,
    fontSize: THEME.fontSize.sm,
    marginBottom: 4,
  },
  dueDate: {
    color: THEME.colors.textSecondary,
    fontSize: THEME.fontSize.sm,
    marginBottom: THEME.spacing.xs,
  },
  overdueText: {
    color: THEME.colors.error,
    fontWeight: '600',
  },
  channelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  channelDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  channelOn: { backgroundColor: THEME.colors.success },
  channelOff: { backgroundColor: THEME.colors.divider },
  channelLabel: {
    color: THEME.colors.textMuted,
    fontSize: THEME.fontSize.xs,
    marginRight: THEME.spacing.sm,
  },
  noChannelTag: {
    color: THEME.colors.warning,
    fontSize: THEME.fontSize.xs,
    fontWeight: '600',
  },
});
