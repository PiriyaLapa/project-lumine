/**
 * TaskCard — displays a single FollowUpTask in the Dashboard list.
 * Field names match openapi.yaml FollowUpTask schema exactly (LOCKED).
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

// Field names match openapi.yaml — do not rename
export interface TaskCardProps {
  id: number;
  customer_id: string;       // LOCKED
  task_type: '2D' | '2W' | '2M';  // LOCKED
  due_date: string;          // LOCKED
  status: 'Pending' | 'Done' | 'Superseded';  // LOCKED
  staff_name: string | null; // LOCKED — null for pre-migration-0005 tasks
  onPress: (taskId: number) => void;
}

const TASK_TYPE_LABELS: Record<string, string> = {
  '2D': 'Experience Check (T+2)',
  '2W': 'Relationship Building (T+14)',
  '2M': 'Retention Check (T+60)',
};

const STATUS_COLORS: Record<string, string> = {
  Pending: '#f59e0b',
  Done: '#22c55e',
  Superseded: '#94a3b8',
};

export default function TaskCard({
  id,
  customer_id,
  task_type,
  due_date,
  status,
  staff_name,
  onPress,
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
      <Text style={styles.customerId}>Customer: {customer_id}</Text>
      {!!staff_name && (
        <Text style={styles.soldBy}>Sold by: {staff_name}</Text>
      )}
      <Text style={[styles.dueDate, isOverdue && styles.overdueText]}>
        Due: {due_date}{isOverdue ? ' — OVERDUE' : ''}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#64748b',
  },
  overdue: {
    borderLeftColor: '#ef4444',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  taskType: {
    color: '#f1f5f9',
    fontWeight: '600',
    fontSize: 14,
    flex: 1,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  customerId: {
    color: '#94a3b8',
    fontSize: 13,
    marginBottom: 2,
  },
  soldBy: {
    color: '#64748b',
    fontSize: 12,
    marginBottom: 4,
  },
  dueDate: {
    color: '#94a3b8',
    fontSize: 13,
  },
  overdueText: {
    color: '#ef4444',
    fontWeight: '600',
  },
});
