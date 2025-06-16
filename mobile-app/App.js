import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';

// Screens
import HomeScreen from './src/screens/HomeScreen';
import NotesScreen from './src/screens/NotesScreen';
import CalendarScreen from './src/screens/CalendarScreen';
import WeatherScreen from './src/screens/WeatherScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="auto" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            let iconName;

            if (route.name === 'Ana Sayfa') {
              iconName = focused ? 'home' : 'home-outline';
            } else if (route.name === 'Notlar') {
              iconName = focused ? 'document-text' : 'document-text-outline';
            } else if (route.name === 'Takvim') {
              iconName = focused ? 'calendar' : 'calendar-outline';
            } else if (route.name === 'Hava Durumu') {
              iconName = focused ? 'cloud' : 'cloud-outline';
            }

            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: '#4A90E2',
          tabBarInactiveTintColor: 'gray',
          tabBarStyle: {
            backgroundColor: 'white',
            borderTopWidth: 1,
            borderTopColor: '#E5E5E5',
            height: 60,
            paddingBottom: 8,
            paddingTop: 8,
          },
          headerStyle: {
            backgroundColor: '#4A90E2',
          },
          headerTintColor: 'white',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        })}
      >
        <Tab.Screen 
          name="Ana Sayfa" 
          component={HomeScreen}
          options={{ 
            headerShown: false 
          }}
        />
        <Tab.Screen 
          name="Notlar" 
          component={NotesScreen}
          options={{ title: 'Notlarım' }}
        />
        <Tab.Screen 
          name="Takvim" 
          component={CalendarScreen}
          options={{ title: 'Takvim' }}
        />
        <Tab.Screen 
          name="Hava Durumu" 
          component={WeatherScreen}
          options={{ title: 'Hava Durumu' }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
