/**
 * AppDrawer — slide-out navigation drawer, opened via Dashboard's hamburger.
 * Custom Modal + core RN Animated (no react-native-gesture-handler/reanimated
 * installed in this project — see plan). Fetches GET /api/v1/auth/me for the
 * profile header each time it opens.
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import { THEME } from '../styles/theme';

const DRAWER_WIDTH = Math.min(300, Dimensions.get('window').width * 0.8);
const ANIM_MS = 220;

type DrawerDestination = 'AutoTouch' | 'FollowUpDashboard' | 'CompletedTasks' | 'Upload';

interface StaffProfile {
  staff_id: number;
  name: string;
  email: string;
  role: string;
}

interface AppDrawerProps {
  visible: boolean;
  onClose: () => void;
  autoTouchDue: number;
  onLogout: () => void;
  navigation: NativeStackNavigationProp<RootStackParamList, 'Dashboard'>;
}

const MAIN_MENU: { screen: DrawerDestination; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { screen: 'AutoTouch', label: 'Auto-Touch', icon: 'flash-outline' },
  { screen: 'FollowUpDashboard', label: 'Follow-Up Report', icon: 'bar-chart-outline' },
  { screen: 'CompletedTasks', label: 'Completed Tasks', icon: 'checkmark-done-outline' },
  { screen: 'Upload', label: 'Upload SAP File', icon: 'cloud-upload-outline' },
];

export default function AppDrawer({ visible, onClose, autoTouchDue, onLogout, navigation }: AppDrawerProps) {
  const [profile, setProfile] = useState<StaffProfile | null>(null);
  const slideAnim = useRef(new Animated.Value(-DRAWER_WIDTH)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!visible) return;
    fetchProfile();
    Animated.parallel([
      Animated.timing(slideAnim, { toValue: 0, duration: ANIM_MS, useNativeDriver: true }),
      Animated.timing(backdropAnim, { toValue: 1, duration: ANIM_MS, useNativeDriver: true }),
    ]).start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  const fetchProfile = async () => {
    try {
      const resp = await client.get('/api/v1/auth/me');
      setProfile(resp.data);
    } catch {
      setProfile(null);
    }
  };

  const closeThen = (after?: () => void) => {
    Animated.parallel([
      Animated.timing(slideAnim, { toValue: -DRAWER_WIDTH, duration: ANIM_MS, useNativeDriver: true }),
      Animated.timing(backdropAnim, { toValue: 0, duration: ANIM_MS, useNativeDriver: true }),
    ]).start(() => {
      onClose();
      after?.();
    });
  };

  const handleNavigate = (screen: DrawerDestination) => {
    closeThen(() => navigation.navigate(screen));
  };

  const handleLogout = () => {
    closeThen(onLogout);
  };

  const initials = profile?.name ? profile.name.trim().charAt(0).toUpperCase() : null;
  const roleLabel = profile?.role === 'store_manager' ? 'Store Manager' : 'Sales Associate';
  const version = Constants.expoConfig?.version ?? '';

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={() => closeThen()}>
      <View style={styles.root}>
        <Animated.View style={[styles.backdrop, { opacity: backdropAnim }]}>
          <TouchableOpacity style={StyleSheet.absoluteFill} activeOpacity={1} onPress={() => closeThen()} />
        </Animated.View>

        <Animated.View style={[styles.drawer, { transform: [{ translateX: slideAnim }] }]}>
          <View style={styles.profileHeader}>
            <View style={styles.avatar}>
              {initials ? (
                <Text style={styles.avatarText}>{initials}</Text>
              ) : (
                <Ionicons name="person" size={24} color={THEME.colors.card} />
              )}
            </View>
            <Text style={styles.profileName} numberOfLines={1}>
              {profile?.name ?? roleLabel}
            </Text>
            <Text style={styles.profileSubtitle} numberOfLines={1}>
              {profile?.email ?? ' '}
            </Text>
          </View>

          <Text style={styles.sectionLabel}>Main Menu</Text>
          {MAIN_MENU.map((item) => (
            <TouchableOpacity
              key={item.screen}
              style={styles.row}
              onPress={() => handleNavigate(item.screen)}
            >
              <Ionicons name={item.icon} size={20} color={THEME.colors.text} style={styles.rowIcon} />
              <Text style={styles.rowLabel}>{item.label}</Text>
              {item.screen === 'AutoTouch' && autoTouchDue > 0 && (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{autoTouchDue}</Text>
                </View>
              )}
            </TouchableOpacity>
          ))}

          <Text style={styles.sectionLabel}>System</Text>
          <TouchableOpacity style={styles.row} onPress={handleLogout}>
            <Ionicons name="log-out-outline" size={20} color={THEME.colors.error} style={styles.rowIcon} />
            <Text style={[styles.rowLabel, { color: THEME.colors.error }]}>Logout</Text>
          </TouchableOpacity>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Lumine{version ? ` v${version}` : ''}</Text>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, flexDirection: 'row' },
  backdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: THEME.colors.overlay },
  drawer: {
    width: DRAWER_WIDTH,
    height: '100%',
    backgroundColor: THEME.colors.background,
    paddingTop: 56,
    paddingHorizontal: THEME.spacing.md,
  },
  profileHeader: {
    paddingBottom: THEME.spacing.lg,
    marginBottom: THEME.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.divider,
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: THEME.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: THEME.spacing.sm,
  },
  avatarText: { color: THEME.colors.card, fontSize: THEME.fontSize.xl, fontWeight: '800' },
  profileName: { color: THEME.colors.text, fontSize: THEME.fontSize.lg, fontWeight: '700' },
  profileSubtitle: { color: THEME.colors.textSecondary, fontSize: THEME.fontSize.sm, marginTop: 2 },
  sectionLabel: {
    color: THEME.colors.textMuted,
    fontSize: THEME.fontSize.xs,
    fontWeight: '700',
    textTransform: 'uppercase',
    marginTop: THEME.spacing.sm,
    marginBottom: THEME.spacing.xs,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  rowIcon: { marginRight: THEME.spacing.sm },
  rowLabel: { flex: 1, color: THEME.colors.text, fontSize: THEME.fontSize.md, fontWeight: '600' },
  badge: {
    minWidth: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: THEME.colors.error,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  badgeText: { color: THEME.colors.card, fontSize: THEME.fontSize.xs, fontWeight: '700' },
  footer: {
    marginTop: 'auto',
    paddingVertical: THEME.spacing.lg,
    borderTopWidth: 1,
    borderTopColor: THEME.colors.divider,
  },
  footerText: { color: THEME.colors.textMuted, fontSize: THEME.fontSize.sm, textAlign: 'center' },
});
