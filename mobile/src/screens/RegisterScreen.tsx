/**
 * RegisterScreen — self-registration for new staff accounts.
 * Field names match openapi.yaml RegisterRequest + AuthResponse exactly.
 * Stores list fetched from GET /api/v1/stores (public endpoint, no JWT needed).
 * On success: stores 4 tokens + navigates to Dashboard (stack reset).
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Modal,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import client, { tokenStorage } from '../api/client';
import { THEME } from '../styles/theme';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'Register'> };

interface Store {
  id: number;   // LOCKED — openapi.yaml Store schema
  name: string; // LOCKED
}

export default function RegisterScreen({ navigation }: Props) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [employeeCode, setEmployeeCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Store picker state
  const [stores, setStores] = useState<Store[]>([]);
  const [storesLoading, setStoresLoading] = useState(true);
  const [storesError, setStoresError] = useState('');
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);
  const [pickerVisible, setPickerVisible] = useState(false);

  // Fetch stores on mount — public endpoint, no JWT required
  const fetchStores = async () => {
    setStoresLoading(true);
    setStoresError('');
    try {
      const resp = await client.get('/api/v1/stores');
      setStores(resp.data);
    } catch {
      setStoresError('Failed to load stores. Please try again.');
    } finally {
      setStoresLoading(false);
    }
  };

  useEffect(() => {
    fetchStores();
  }, []);

  const handleRegister = async () => {
    setError('');

    if (!fullName.trim()) { setError('Full name is required.'); return; }
    if (!email.trim()) { setError('Email address is required.'); return; }
    if (!password) { setError('Password is required.'); return; }
    if (password.length < 8) { setError('Password must be at least 8 characters.'); return; }
    if (password !== confirmPassword) { setError('Passwords do not match.'); return; }
    if (!employeeCode.trim()) { setError('SAP employee code is required.'); return; }
    if (!selectedStore) { setError('Please select your store.'); return; }

    setLoading(true);
    try {
      // Field names match openapi.yaml RegisterRequest
      const response = await client.post('/api/v1/auth/register', {
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        confirm_password: confirmPassword,
        // GH #27: self-registration is always sales_associate — backend ignores this
        // field's value regardless, but it stays required by openapi.yaml's contract.
        role: 'sales_associate',
        store_id: selectedStore.id,
        employee_code: employeeCode.trim(),
      });

      const { access_token, refresh_token, staff_id, role: userRole } = response.data;

      await tokenStorage.setTokens(access_token, refresh_token);
      await AsyncStorage.setItem('staff_id', String(staff_id));
      await AsyncStorage.setItem('role', userRole);

      // Reset the stack so Dashboard is the only screen (no back to Register/Login)
      navigation.reset({ index: 0, routes: [{ name: 'Dashboard' }] });
    } catch (err: any) {
      if (err.response?.status === 409) {
        const detail = err.response.data?.detail ?? '';
        if (detail.includes('employee code')) {
          setError('This employee code is already registered. Contact your manager.');
        } else {
          setError('An account with this email already exists.');
        }
      } else if (err.response?.status === 422) {
        const detail = err.response.data?.detail;
        if (Array.isArray(detail) && detail[0]?.msg) {
          setError(detail[0].msg.replace('Value error, ', ''));
        } else {
          setError('Please check your details and try again.');
        }
      } else if (!err.response) {
        setError('Cannot connect to server. Check your network connection.');
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Store picker trigger — looks like other input rows
  // ---------------------------------------------------------------------------
  const renderStorePicker = () => {
    if (storesLoading) {
      return (
        <View style={[styles.inputRow, styles.pickerRow]}>
          <Ionicons name="business-outline" size={18} color={THEME.colors.textSecondary} style={styles.icon} />
          <ActivityIndicator size="small" color={THEME.colors.primary} style={{ marginRight: 8 }} />
          <Text style={styles.pickerPlaceholder}>Loading stores...</Text>
        </View>
      );
    }

    if (storesError) {
      return (
        <TouchableOpacity style={[styles.inputRow, styles.pickerRow]} onPress={fetchStores}>
          <Ionicons name="business-outline" size={18} color={THEME.colors.error} style={styles.icon} />
          <Text style={[styles.pickerPlaceholder, { color: THEME.colors.error, flex: 1 }]}>
            Failed to load stores. Please try again.
          </Text>
          <Ionicons name="refresh-outline" size={18} color={THEME.colors.error} />
        </TouchableOpacity>
      );
    }

    return (
      <TouchableOpacity
        style={[styles.inputRow, styles.pickerRow]}
        onPress={() => setPickerVisible(true)}
      >
        <Ionicons name="business-outline" size={18} color={THEME.colors.textSecondary} style={styles.icon} />
        <Text style={[styles.pickerText, !selectedStore && styles.pickerPlaceholder]}>
          {selectedStore ? selectedStore.name : 'Select your store'}
        </Text>
        <Ionicons name="chevron-down-outline" size={18} color={THEME.colors.textSecondary} />
      </TouchableOpacity>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.card}>
          <Text style={styles.sparkle}>✦</Text>
          <Text style={styles.brand}>LUMINE</Text>
          <Text style={styles.subtitle}>Create your account</Text>

          {/* Full Name */}
          <View style={styles.inputRow}>
            <Ionicons name="person-outline" size={18} color={THEME.colors.textSecondary} style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Full Name"
              placeholderTextColor={THEME.colors.textMuted}
              value={fullName}
              onChangeText={setFullName}
              autoCapitalize="words"
            />
          </View>

          {/* Email */}
          <View style={styles.inputRow}>
            <Ionicons name="mail-outline" size={18} color={THEME.colors.textSecondary} style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Email Address"
              placeholderTextColor={THEME.colors.textMuted}
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
          </View>

          {/* Password */}
          <View style={styles.inputRow}>
            <Ionicons name="lock-closed-outline" size={18} color={THEME.colors.textSecondary} style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Password (min 8 characters)"
              placeholderTextColor={THEME.colors.textMuted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(v => !v)} style={styles.eyeBtn}>
              <Ionicons name={showPassword ? 'eye-outline' : 'eye-off-outline'} size={18} color={THEME.colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {/* Confirm Password */}
          <View style={styles.inputRow}>
            <Ionicons name="lock-closed-outline" size={18} color={THEME.colors.textSecondary} style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Confirm Password"
              placeholderTextColor={THEME.colors.textMuted}
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showConfirm}
            />
            <TouchableOpacity onPress={() => setShowConfirm(v => !v)} style={styles.eyeBtn}>
              <Ionicons name={showConfirm ? 'eye-outline' : 'eye-off-outline'} size={18} color={THEME.colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {/* SAP Employee Code */}
          <View style={styles.inputRow}>
            <Ionicons name="barcode-outline" size={18} color={THEME.colors.textSecondary} style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="SAP Employee Code (e.g. 56546)"
              placeholderTextColor={THEME.colors.textMuted}
              value={employeeCode}
              onChangeText={setEmployeeCode}
              autoCapitalize="none"
              keyboardType="numeric"
            />
          </View>

          {/* Store Picker */}
          <Text style={styles.label}>Store</Text>
          {renderStorePicker()}

          {error !== '' && <Text style={styles.errorText}>{error}</Text>}

          <TouchableOpacity
            style={[styles.button, loading && styles.disabled]}
            onPress={handleRegister}
            disabled={loading}
          >
            <Text style={styles.buttonText}>{loading ? 'Creating account...' : 'Register →'}</Text>
          </TouchableOpacity>

          <View style={styles.divider} />

          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.linkText}>
              Already have an account?{' '}
              <Text style={styles.linkGold}>Sign In</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Store selection modal */}
      <Modal
        visible={pickerVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setPickerVisible(false)}
      >
        <TouchableOpacity
          style={styles.modalBackdrop}
          activeOpacity={1}
          onPress={() => setPickerVisible(false)}
        >
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Select Store</Text>
            <FlatList
              data={stores}
              keyExtractor={item => String(item.id)}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={[
                    styles.storeItem,
                    selectedStore?.id === item.id && styles.storeItemActive,
                  ]}
                  onPress={() => {
                    setSelectedStore(item);
                    setPickerVisible(false);
                  }}
                >
                  <Text
                    style={[
                      styles.storeItemText,
                      selectedStore?.id === item.id && styles.storeItemTextActive,
                    ]}
                  >
                    {item.name}
                  </Text>
                  {selectedStore?.id === item.id && (
                    <Ionicons name="checkmark" size={18} color={THEME.colors.primary} />
                  )}
                </TouchableOpacity>
              )}
              ItemSeparatorComponent={() => <View style={styles.storeSeparator} />}
            />
            <TouchableOpacity
              style={styles.modalClose}
              onPress={() => setPickerVisible(false)}
            >
              <Text style={styles.modalCloseText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.colors.background },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: THEME.spacing.lg, paddingVertical: 40 },
  card: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.lg,
    padding: THEME.spacing.xl,
    shadowColor: THEME.colors.primaryShadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 8,
  },
  sparkle: { textAlign: 'center', fontSize: THEME.fontSize.xl, color: THEME.colors.primary, marginBottom: THEME.spacing.sm },
  brand: {
    textAlign: 'center',
    fontSize: THEME.fontSize.brand,
    fontWeight: '800',
    color: THEME.colors.text,
    letterSpacing: 6,
    marginBottom: 6,
  },
  subtitle: { textAlign: 'center', fontSize: THEME.fontSize.sm, color: THEME.colors.textSecondary, marginBottom: 28 },
  label: { fontSize: THEME.fontSize.xs, color: THEME.colors.textSecondary, fontWeight: '600', marginBottom: THEME.spacing.sm, marginTop: 2 },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: THEME.colors.input,
    borderRadius: THEME.radius.md,
    marginBottom: 14,
    paddingHorizontal: 14,
  },
  pickerRow: { paddingVertical: 14 },
  icon: { marginRight: THEME.spacing.sm },
  input: { flex: 1, color: THEME.colors.text, fontSize: THEME.fontSize.md, paddingVertical: 14 },
  eyeBtn: { padding: 4 },
  pickerText: { flex: 1, color: THEME.colors.text, fontSize: THEME.fontSize.md },
  pickerPlaceholder: { flex: 1, color: THEME.colors.textMuted, fontSize: THEME.fontSize.md },
  errorText: { color: THEME.colors.error, fontSize: THEME.fontSize.sm, marginBottom: 12, textAlign: 'center' },
  button: {
    backgroundColor: THEME.colors.primary,
    borderRadius: THEME.radius.pill,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: THEME.spacing.sm,
  },
  disabled: { opacity: 0.5 },
  buttonText: { color: THEME.colors.card, fontSize: THEME.fontSize.lg, fontWeight: '700' },
  divider: { height: 1, backgroundColor: THEME.colors.divider, marginVertical: 20 },
  linkText: { textAlign: 'center', color: THEME.colors.textSecondary, fontSize: 14 },
  linkGold: { color: THEME.colors.primary, fontWeight: '600' },

  // Modal
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    paddingHorizontal: THEME.spacing.lg,
  },
  modalCard: {
    backgroundColor: THEME.colors.card,
    borderRadius: THEME.radius.lg,
    paddingTop: THEME.spacing.lg,
    paddingBottom: THEME.spacing.sm,
    maxHeight: '70%',
    shadowColor: THEME.colors.primaryShadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 12,
  },
  modalTitle: {
    fontSize: THEME.fontSize.lg,
    fontWeight: '700',
    color: THEME.colors.text,
    textAlign: 'center',
    marginBottom: THEME.spacing.md,
    paddingHorizontal: THEME.spacing.lg,
  },
  storeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: THEME.spacing.lg,
  },
  storeItemActive: { backgroundColor: '#FDF6EC' },
  storeItemText: { fontSize: THEME.fontSize.md, color: THEME.colors.text, flex: 1 },
  storeItemTextActive: { color: THEME.colors.primary, fontWeight: '600' },
  storeSeparator: { height: 1, backgroundColor: THEME.colors.divider, marginHorizontal: THEME.spacing.lg },
  modalClose: {
    margin: THEME.spacing.md,
    paddingVertical: 14,
    borderRadius: THEME.radius.pill,
    backgroundColor: THEME.colors.surface,
    alignItems: 'center',
  },
  modalCloseText: { color: THEME.colors.textSecondary, fontSize: THEME.fontSize.md, fontWeight: '600' },
});
