/**
 * LoginScreen — light luxury design.
 * All existing logic preserved: error handling, interceptor fix, 4-token storage.
 * Field names match openapi.yaml LoginRequest + AuthResponse exactly.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import client, { tokenStorage } from '../api/client';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'Login'> };

export default function LoginScreen({ navigation }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    setError('');

    if (!email.trim() || !password.trim()) {
      setError('Please enter your email and password.');
      return;
    }

    setLoading(true);
    try {
      // Field names match openapi.yaml LoginRequest
      const response = await client.post('/api/v1/auth/login', { email, password });
      const { access_token, refresh_token, staff_id, role } = response.data;

      // Store all 4 values — access/refresh via tokenStorage, id/role directly
      await tokenStorage.setTokens(access_token, refresh_token);
      await AsyncStorage.setItem('staff_id', String(staff_id));
      await AsyncStorage.setItem('role', role);

      navigation.replace('Dashboard');
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Invalid email or password.');
      } else if (err.response) {
        setError(err.response.data?.detail ?? 'Login failed. Please try again.');
      } else {
        setError('Cannot connect to server. Check your network connection.');
      }
    } finally {
      setLoading(false);
    }
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
          <Text style={styles.subtitle}>Luxury Retail CRM</Text>

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

          <View style={styles.inputRow}>
            <Ionicons name="lock-closed-outline" size={18} color="#9A9A9A" style={styles.icon} />
            <TextInput
              style={styles.input}
              placeholder="Password"
              placeholderTextColor="#B0A898"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeBtn}>
              <Ionicons
                name={showPassword ? 'eye-outline' : 'eye-off-outline'}
                size={18}
                color="#9A9A9A"
              />
            </TouchableOpacity>
          </View>

          {error !== '' && <Text style={styles.errorText}>{error}</Text>}

          <TouchableOpacity
            style={[styles.button, loading && styles.disabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            <Text style={styles.buttonText}>{loading ? 'Signing in...' : 'Login →'}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.forgotBtn} disabled>
            <Text style={styles.forgotText}>Forgot password? Contact your manager.</Text>
          </TouchableOpacity>

          <View style={styles.divider} />

          <TouchableOpacity onPress={() => navigation.navigate('Register')}>
            <Text style={styles.linkText}>
              Don't have an account?{' '}
              <Text style={styles.linkGold}>Register</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAF7F2' },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
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
  subtitle: { textAlign: 'center', fontSize: 13, color: '#9A9A9A', marginBottom: 32 },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F2EC',
    borderRadius: 12,
    marginBottom: 14,
    paddingHorizontal: 14,
  },
  icon: { marginRight: 8 },
  input: { flex: 1, color: '#1A1A1A', fontSize: 15, paddingVertical: 14 },
  eyeBtn: { padding: 4 },
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
  forgotBtn: { marginTop: 16, alignItems: 'center' },
  forgotText: { color: '#B0A898', fontSize: 12 },
  divider: { height: 1, backgroundColor: '#F0EBE3', marginVertical: 20 },
  linkText: { textAlign: 'center', color: '#9A9A9A', fontSize: 14 },
  linkGold: { color: '#C9974A', fontWeight: '600' },
});
