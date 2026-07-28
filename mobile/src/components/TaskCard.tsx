/**
 * TaskCard — displays a single FollowUpTask in the Dashboard list.
 * Field names match openapi.yaml FollowUpTask schema exactly (LOCKED).
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { THEME } from '../styles/theme';

// Field names match openapi.yaml — do not rename
export interface TaskCardProps {
  id: number;
  customer_id: string;       // LOCKED
  customer_name: string | null; // LOCKED — null for pre-migration-0010 tasks or absent from source file
  task_type: '2D' | '2W' | '2M';  // LOCKED
  due_date: string;          // LOCKED
  status: 'Pending' | 'Done' | 'Superseded';  // LOCKED
  staff_name: string | null; // LOCKED — null for pre-migration-0005 tasks
  onPress: (taskId: number) => void;
  onCustomerPress?: (customerId: string, customerName: string | null) => void;
}

const TASK_TYPE_LABELS: Record<string, string> = {
  '2D': 'Experience Check (T+2)',
  '2W': 'Relationship Building (T+14)',
  '2M': 'Retention Check (T+60)',
};

const STATUS_COLORS: Record<string, string> = {
  Pending: '#d97706',
  Done: '#16a34a',
  Superseded: '#9A9A9A',
};

export default function TaskCard({
  id,
  customer_id,
  customer_name,
  task_type,
  due_date,
  status,
  staff_name,
  onPress,
  onCustomerPress,
}: TaskCardProps) {
  const isOverdue =
    status === 'Pending' && new Date(due_date) < new Date();

  return (
    <TouchableOpacity
      style={[styles.card, isOverdue && styles.overdue]}
      onPress={() => onPress(id)}
      activeOpacity={0.8}
    >
      <View style={styles.header}>
        <Text style={styles.taskType}>{TASK_TYPE_LABELS[task_type]}</Text>
        <View style={[styles.badge, { backgroundColor: STATUS_COLORS[status] }]}>
          <Text style={styles.badgeText}>{status}</Text>
        </View>
      </View>
      <TouchableOpacity
        disabled={!onCustomerPress}
        onPress={() => onCustomerPress?.(customer_id, customer_name)}
        hitSlop={{ top: 4, bottom: 4, left: 4, right: 4 }}
      >
        {!!customer_name && <Text style={styles.customerName}>{customer_name}</Text>}
        <Text style={styles.customerId}>Customer: {customer_id}</Text>
      </TouchableOpacity>
      <Text style={[styles.dueDate, isOverdue && styles.overdueText]}>
        Due: {due_date}{isOverdue ? ' — OVERDUE' : ''}
      </Text>
      {!!staff_name && (
        <Text style={styles.soldBy}>Sold by: {staff_name}</Text>
      )}
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
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
  },
  badgeText: {
    color: THEME.colors.card,
    fontSize: THEME.fontSize.xs,
    fontWeight: '700',
  },
  customerName: {
    color: THEME.colors.text,
    fontWeight: '700',
    fontSize: THEME.fontSize.md,
    marginBottom: 2,
  },
  customerId: {
    color: THEME.colors.textSecondary,
    fontSize: THEME.fontSize.sm,
    marginBottom: 2,
  },
  soldBy: {
    color: THEME.colors.soldBy,
    fontSize: THEME.fontSize.xs,
    marginBottom: 4,
  },
  dueDate: {
    color: THEME.colors.textSecondary,
    fontSize: THEME.fontSize.sm,
  },
  overdueText: {
    color: THEME.colors.error,
    fontWeight: '600',
  },
});
