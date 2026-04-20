/**
 * BarcodeScreen — customer barcode for MOCCA iPad scanning.
 * SRS §5 FR-05: display scannable barcode for customer_id.
 * Barcode is cached — works offline (SRS §7 NFR-05).
 * customer_id field name LOCKED — matches openapi.yaml.
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import BarcodeDisplay from '../components/BarcodeDisplay';
import OfflineBanner from '../components/OfflineBanner';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Barcode'>;
  route: RouteProp<RootStackParamList, 'Barcode'>;
};

export default function BarcodeScreen({ navigation, route }: Props) {
  const { customer_id } = route.params;  // LOCKED field name

  return (
    <View style={styles.container}>
      <OfflineBanner />

      <TouchableOpacity style={styles.back} onPress={() => navigation.goBack()}>
        <Text style={styles.backText}>← Back</Text>
      </TouchableOpacity>

      <Text style={styles.title}>Customer Barcode</Text>
      <Text style={styles.subtitle}>Show this to the MOCCA iPad scanner</Text>

      <BarcodeDisplay customer_id={customer_id} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  back: { padding: 20, paddingTop: 56 },
  backText: { color: '#6366f1', fontSize: 16 },
  title: { fontSize: 24, fontWeight: '800', color: '#f1f5f9', textAlign: 'center', marginTop: 8 },
  subtitle: { color: '#64748b', textAlign: 'center', marginTop: 8, fontSize: 14, marginBottom: 8 },
});
