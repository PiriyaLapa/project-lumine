/**
 * LoginScreen — email + password → JWT token pair.
 * On success: stores tokens, navigates to Dashboard.
 * Field names match openapi.yaml LoginRequest + AuthResponse exactly.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import client from '../api/client';
import { tokenStorage } from '../api/client';

type Props = { navigation: NativeStackNavigationProp<RootStackParamList, 'Login'> };

export default function LoginScreen({ navigation }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter email and password.');
      return;
    }

    setLoading(true);
    try {
      // Field names match openapi.yaml LoginRequest
      const response = await client.post('/api/v1/auth/login', { email, password });
      const { access_token, refresh_token } = response.data;

      await tokenStorage.setTokens(access_token, refresh_token);
      navigation.replace('Dashboard');
    } catch (error: any) {
      const message = error.response?.data?.detail ?? 'Login failed. Please try again.';
      Alert.alert('Login Failed', message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.card}>
        <Text style={styles.title}>Lumine</Text>
        <Text style={styles.subtitle}>Luxury Retail CRM</Text>

        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor="#64748b"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />

        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#64748b"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        <TouchableOpacity
          style={[styles.button, loading && styles.disabled]}
          onPress={handleLogin}
          disabled={loading}
        >
          <Text style={styles.buttonText}>{loading ? 'Signing in...' : 'Sign In'}</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', justifyContent: 'center', padding: 24 },
  card: { backgroundColor: '#1e293b', borderRadius: 16, padding: 28 },
  title: { fontSize: 32, fontWeight: '800', color: '#f1f5f9', textAlign: 'center', marginBottom: 4 },
  subtitle: { fontSize: 14, color: '#64748b', textAlign: 'center', marginBottom: 32 },
  input: {
    backgroundColor: '#0f172a',
    color: '#f1f5f9',
    borderRadius: 8,
    padding: 14,
    fontSize: 15,
    marginBottom: 14,
  },
  button: { backgroundColor: '#6366f1', borderRadius: 8, padding: 16, alignItems: 'center', marginTop: 8 },
  disabled: { opacity: 0.5 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
