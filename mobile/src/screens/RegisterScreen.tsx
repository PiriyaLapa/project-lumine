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
  const [role, setRole] = useState<'sales_associate' | 'store_manager'>('sales_associate');
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
    if (!selectedStore) { setError('Please select your store.'); return; }

    setLoading(true);
    try {
      // Field names match openapi.yaml RegisterRequest
      const response = await client.post('/api/v1/auth/register', {
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        confirm_password: confirmPassword,
        role,
        store_id: selectedStore.id,
      });

      const { access_token, refresh_token, staff_id, role: userRole } = response.data;

      await tokenStorage.setTokens(access_token, refresh_token);
      await AsyncStorage.setItem('staff_id', String(staff_id));
      await AsyncStorage.setItem('role', userRole);

      // Reset the stack so Dashboard is the only screen (no back to Register/Login)
      navigation.reset({ index: 0, routes: [{ name: 'Dashboard' }] });
    } catch (err: any) {
      if (err.response?.status === 409) {
        setError('An account with this email already exists.');
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
          <Ionicons name="business-outline" size={18} color="#9A9A9A" style={styles.icon} />
          <ActivityIndicator size="small" color="#C9974A" style={{ marginRight: 8 }} />
          <Text style={styles.pickerPlaceholder}>Loading stores...</Text>
        </View>
      );
    }

    if (storesError) {
      return (
        <TouchableOpacity style={[styles.inputRow, styles.pickerRow]} onPress={fetchStores}>
          <Ionicons name="business-outline" size={18} color="#DC2626" style={styles.icon} />
          <Text style={[styles.pickerPlaceholder, { color: '#DC2626', flex: 1 }]}>
            Failed to load stores. Please try again.
          </Text>
          <Ionicons name="refresh-outline" size={18} color="#DC2626" />
        </TouchableOpacity>
      );
    }

    return (
      <TouchableOpacity
        style={[styles.inputRow, styles.pickerRow]}
        onPress={() => setPickerVisible(true)}
      >
        <Ionicons name="business-outline" size={18} color="#9A9A9A" style={styles.icon} />
        <Text style={[styles.pickerText, !selectedStore && styles.pickerPlaceholder]}>
          {selectedStore ? selectedStore.name : 'Select your store'}
        </Text>
        <Ionicons name="chevron-down-outline" size={18} color="#9A9A9A" />
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
            <Ionicons name="person-outline" size={18} color="#9A9A9A" style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Full Name"
              placeholderTextColor="#B0A898"
              value={fullName}
              onChangeText={setFullName}
              autoCapitalize="words"
            />
          </View>

          {/* Email */}
          <View style={styles.inputRow}>
            <Ionicons name="mail-outline" size={18} color="#9A9A9A" style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Email Address"
              placeholderTextColor="#B0A898"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
          </View>

          {/* Password */}
          <View style={styles.inputRow}>
            <Ionicons name="lock-closed-outline" size={18} color="#9A9A9A" style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Password (min 8 characters)"
              placeholderTextColor="#B0A898"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(v => !v)} style={styles.eyeBtn}>
              <Ionicons name={showPassword ? 'eye-outline' : 'eye-off-outline'} size={18} color="#9A9A9A" />
            </TouchableOpacity>
          </View>

          {/* Confirm Password */}
          <View style={styles.inputRow}>
            <Ionicons name="lock-closed-outline" size={18} color="#9A9A9A" style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Confirm Password"
              placeholderTextColor="#B0A898"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showConfirm}
            />
            <TouchableOpacity onPress={() => setShowConfirm(v => !v)} style={styles.eyeBtn}>
              <Ionicons name={showConfirm ? 'eye-outline' : 'eye-off-outline'} size={18} color="#9A9A9A" />
            </TouchableOpacity>
          </View>

          {/* Role Picker */}
          <Text style={styles.label}>Role</Text>
          <View style={styles.roleRow}>
            <TouchableOpacity
              style={[styles.roleBtn, role === 'sales_associate' && styles.roleBtnActive]}
              onPress={() => setRole('sales_associate')}
            >
              <Text style={[styles.roleBtnText, role === 'sales_associate' && styles.roleBtnTextActive]}>
                Sales Associate
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.roleBtn, role === 'store_manager' && styles.roleBtnActive]}
              onPress={() => setRole('store_manager')}
            >
              <Text style={[styles.roleBtnText, role === 'store_manager' && styles.roleBtnTextActive]}>
                Store Manager
              </Text>
            </TouchableOpacity>
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
                    <Ionicons name="checkmark" size={18} color="#C9974A" />
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
  container: { flex: 1, backgroundColor: '#FAF7F2' },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24, paddingVertical: 40 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 32,
    shadowColor: '#C9974A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 8,
  },
  sparkle: { textAlign: 'center', fontSize: 20, color: '#C9974A', marginBottom: 8 },
  brand: {
    textAlign: 'center',
    fontSize: 32,
    fontWeight: '800',
    color: '#1A1A1A',
    letterSpacing: 6,
    marginBottom: 6,
  },
  subtitle: { textAlign: 'center', fontSize: 13, color: '#9A9A9A', marginBottom: 28 },
  label: { fontSize: 12, color: '#9A9A9A', fontWeight: '600', marginBottom: 8, marginTop: 2 },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F2EC',
    borderRadius: 12,
    marginBottom: 14,
    paddingHorizontal: 14,
  },
  pickerRow: { paddingVertical: 14 },
  icon: { marginRight: 8 },
  input: { flex: 1, color: '#1A1A1A', fontSize: 15, paddingVertical: 14 },
  eyeBtn: { padding: 4 },
  pickerText: { flex: 1, color: '#1A1A1A', fontSize: 15 },
  pickerPlaceholder: { flex: 1, color: '#B0A898', fontSize: 15 },
  roleRow: { flexDirection: 'row', gap: 10, marginBottom: 14 },
  roleBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: '#F5F2EC',
    alignItems: 'center',
  },
  roleBtnActive: { backgroundColor: '#C9974A' },
  roleBtnText: { color: '#9A9A9A', fontSize: 13, fontWeight: '600' },
  roleBtnTextActive: { color: '#FFFFFF' },
  errorText: { color: '#DC2626', fontSize: 13, marginBottom: 12, textAlign: 'center' },
  button: {
    backgroundColor: '#C9974A',
    borderRadius: 50,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  disabled: { opacity: 0.5 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  divider: { height: 1, backgroundColor: '#F0EBE3', marginVertical: 20 },
  linkText: { textAlign: 'center', color: '#9A9A9A', fontSize: 14 },
  linkGold: { color: '#C9974A', fontWeight: '600' },

  // Modal
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  modalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingTop: 24,
    paddingBottom: 8,
    maxHeight: '70%',
    shadowColor: '#C9974A',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 12,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A1A',
    textAlign: 'center',
    marginBottom: 16,
    paddingHorizontal: 24,
  },
  storeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  storeItemActive: { backgroundColor: '#FDF6EC' },
  storeItemText: { fontSize: 15, color: '#1A1A1A', flex: 1 },
  storeItemTextActive: { color: '#C9974A', fontWeight: '600' },
  storeSeparator: { height: 1, backgroundColor: '#F0EBE3', marginHorizontal: 24 },
  modalClose: {
    margin: 16,
    paddingVertical: 14,
    borderRadius: 50,
    backgroundColor: '#F5F2EC',
    alignItems: 'center',
  },
  modalCloseText: { color: '#9A9A9A', fontSize: 15, fontWeight: '600' },
});
