/**
 * BarcodeDisplay — renders a scannable QR code for a customer_id.
 * Used by BarcodeScreen for MOCCA iPad integration (SRS §5 FR-05).
 * customer_id field name LOCKED — matches openapi.yaml.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import QRCode from 'react-native-qrcode-svg';

interface BarcodeDisplayProps {
  customer_id: string;  // LOCKED
}

export default function BarcodeDisplay({ customer_id }: BarcodeDisplayProps) {
  return (
    <View style={styles.container}>
      <QRCode
        value={customer_id}
        size={220}
        backgroundColor="#ffffff"
        color="#0f172a"
      />
      <Text style={styles.label}>Customer ID</Text>
      <Text style={styles.customerId}>{customer_id}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#ffffff',
    borderRadius: 16,
    margin: 24,
  },
  label: {
    marginTop: 16,
    fontSize: 12,
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  customerId: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0f172a',
    marginTop: 4,
  },
});
