/**
 * OfflineBanner — shown when device has no internet.
 * SRS §7 NFR-05: "Show a visible 'Offline Mode' banner when no internet detected."
 * No silent sync. User must see this clearly.
 */

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import * as Network from 'expo-network';

export default function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    let mounted = true;

    const check = async () => {
      const state = await Network.getNetworkStateAsync();
      if (mounted) setIsOffline(!state.isConnected || !state.isInternetReachable);
    };

    check();
    const interval = setInterval(check, 5000); // poll every 5s
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <View style={styles.banner}>
      <Text style={styles.text}>⚠ Offline Mode — some features unavailable</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: '#f59e0b',
    paddingVertical: 6,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  text: {
    color: '#1c1917',
    fontWeight: '600',
    fontSize: 13,
  },
});
