/**
 * AppNavigator — root navigation stack.
 * Listens to authEvents.onLogout to force redirect to Login on token expiry.
 * SRS §7 NFR-02: refresh_token expired → force logout → redirect to login.
 */

import React, { useEffect, useState, useRef } from 'react';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import LoginScreen from '../screens/LoginScreen';
import DashboardScreen from '../screens/DashboardScreen';
import TaskDetailScreen from '../screens/TaskDetailScreen';
import EvidenceScreen from '../screens/EvidenceScreen';
import BarcodeScreen from '../screens/BarcodeScreen';
import UploadScreen from '../screens/UploadScreen';
import UploadHistoryScreen from '../screens/UploadHistoryScreen';
import RegisterScreen from '../screens/RegisterScreen';

import { tokenStorage, authEvents } from '../api/client';

// ---------------------------------------------------------------------------
// Type definitions — field names match openapi.yaml FollowUpTask schema
// ---------------------------------------------------------------------------

export type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  Dashboard: undefined;
  TaskDetail: { taskId: number };
  Evidence: { taskId: number };
  Barcode: { customer_id: string };   // LOCKED field name from openapi.yaml
  Upload: undefined;
  UploadHistory: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const navigationRef = useRef<NavigationContainerRef<RootStackParamList>>(null);

  // Check for existing token on app start
  useEffect(() => {
    tokenStorage.getAccessToken().then((token) => {
      setIsAuthenticated(!!token);
    });
  }, []);

  // Listen for forced logout (refresh token expired)
  useEffect(() => {
    const unsubscribe = authEvents.onLogout(() => {
      navigationRef.current?.reset({ index: 0, routes: [{ name: 'Login' }] });
      setIsAuthenticated(false);
    });
    return unsubscribe;
  }, []);

  // Loading state — avoid flash of wrong screen
  if (isAuthenticated === null) return null;

  return (
    <NavigationContainer ref={navigationRef}>
      <Stack.Navigator
        initialRouteName={isAuthenticated ? 'Dashboard' : 'Login'}
        screenOptions={{ headerShown: false }}
      >
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="Dashboard" component={DashboardScreen} />
        <Stack.Screen name="TaskDetail" component={TaskDetailScreen} />
        <Stack.Screen name="Evidence" component={EvidenceScreen} />
        <Stack.Screen name="Barcode" component={BarcodeScreen} />
        <Stack.Screen name="Upload" component={UploadScreen} />
        <Stack.Screen name="UploadHistory" component={UploadHistoryScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
