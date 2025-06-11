import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import apiService from '../services/api';

export default function WeatherScreen() {
  const [weather, setWeather] = useState(null);
  const [city, setCity] = useState('Istanbul');
  const [inputCity, setInputCity] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Hava durumu yükle
  const loadWeather = async (cityName = city) => {
    try {
      setIsLoading(true);
      const response = await apiService.getWeather(cityName);
      setWeather(response);
      setCity(cityName);
    } catch (error) {
      console.error('Hava durumu yüklenemedi:', error);
      Alert.alert('Hata', 'Hava durumu bilgisi alınamadı');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadWeather();
  }, []);

  // Yenile
  const onRefresh = async () => {
    setRefreshing(true);
    await loadWeather();
    setRefreshing(false);
  };

  // Şehir değiştir
  const changeCity = () => {
    if (!inputCity.trim()) {
      Alert.alert('Hata', 'Şehir adı giriniz');
      return;
    }
    loadWeather(inputCity.trim());
    setInputCity('');
  };

  // Hava durumu ikonu
  const getWeatherIcon = (condition) => {
    const lowerCondition = condition?.toLowerCase() || '';
    if (lowerCondition.includes('clear') || lowerCondition.includes('sunny')) {
      return 'sunny';
    } else if (lowerCondition.includes('cloud')) {
      return 'cloudy';
    } else if (lowerCondition.includes('rain')) {
      return 'rainy';
    } else if (lowerCondition.includes('snow')) {
      return 'snow';
    } else if (lowerCondition.includes('storm')) {
      return 'thunderstorm';
    }
    return 'partly-sunny';
  };

  // Hava durumu rengi
  const getWeatherColor = (condition) => {
    const lowerCondition = condition?.toLowerCase() || '';
    if (lowerCondition.includes('clear') || lowerCondition.includes('sunny')) {
      return '#FFD700';
    } else if (lowerCondition.includes('cloud')) {
      return '#87CEEB';
    } else if (lowerCondition.includes('rain')) {
      return '#4682B4';
    }
    return '#4A90E2';
  };

  if (isLoading && !weather) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Ionicons name="cloud-download-outline" size={64} color="#CCC" />
        <Text style={styles.loadingText}>Hava durumu yükleniyor...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Şehir Seçimi */}
      <View style={styles.citySelector}>
        <TextInput
          style={styles.cityInput}
          value={inputCity}
          onChangeText={setInputCity}
          placeholder="Şehir adı giriniz"
          onSubmitEditing={changeCity}
        />
        <TouchableOpacity style={styles.searchButton} onPress={changeCity}>
          <Ionicons name="search" size={20} color="white" />
        </TouchableOpacity>
      </View>

      {weather && (
        <View style={styles.weatherContainer}>
          {/* Ana Hava Durumu Kartı */}
          <View style={[
            styles.mainWeatherCard,
            { backgroundColor: getWeatherColor(weather.condition) }
          ]}>
            <View style={styles.cityHeader}>
              <Text style={styles.cityName}>{weather.city}</Text>
              <Text style={styles.date}>
                {new Date().toLocaleDateString('tr-TR', {
                  weekday: 'long',
                  day: 'numeric',
                  month: 'long',
                })}
              </Text>
            </View>

            <View style={styles.mainWeatherInfo}>
              <View style={styles.temperatureContainer}>
                <Text style={styles.temperature}>
                  {Math.round(weather.temperature)}°C
                </Text>
                <Text style={styles.feelsLike}>
                  Hissedilen: {Math.round(weather.feels_like || weather.temperature)}°C
                </Text>
              </View>

              <View style={styles.weatherIconContainer}>
                <Ionicons
                  name={getWeatherIcon(weather.condition)}
                  size={80}
                  color="white"
                />
                <Text style={styles.condition}>{weather.condition}</Text>
              </View>
            </View>
          </View>

          {/* Detay Bilgileri */}
          <View style={styles.detailsContainer}>
            <View style={styles.detailRow}>
              <View style={styles.detailItem}>
                <Ionicons name="water-outline" size={24} color="#4A90E2" />
                <Text style={styles.detailLabel}>Nem</Text>
                <Text style={styles.detailValue}>
                  {weather.humidity || 'N/A'}%
                </Text>
              </View>

              <View style={styles.detailItem}>
                <Ionicons name="speedometer-outline" size={24} color="#4A90E2" />
                <Text style={styles.detailLabel}>Rüzgar</Text>
                <Text style={styles.detailValue}>
                  {weather.wind_speed || 'N/A'} km/h
                </Text>
              </View>

              <View style={styles.detailItem}>
                <Ionicons name="barbell-outline" size={24} color="#4A90E2" />
                <Text style={styles.detailLabel}>Basınç</Text>
                <Text style={styles.detailValue}>
                  {weather.pressure || 'N/A'} hPa
                </Text>
              </View>
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
  },
  citySelector: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  cityInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E5E5',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  searchButton: {
    marginLeft: 8,
    backgroundColor: '#4A90E2',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  weatherContainer: {
    padding: 16,
  },
  mainWeatherCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  cityHeader: {
    alignItems: 'center',
    marginBottom: 20,
  },
  cityName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
  date: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 4,
  },
  mainWeatherInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  temperatureContainer: {
    flex: 1,
  },
  temperature: {
    fontSize: 48,
    fontWeight: 'bold',
    color: 'white',
  },
  feelsLike: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 4,
  },
  weatherIconContainer: {
    alignItems: 'center',
  },
  condition: {
    fontSize: 16,
    color: 'white',
    marginTop: 8,
    textAlign: 'center',
  },
  detailsContainer: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  detailItem: {
    alignItems: 'center',
    flex: 1,
  },
  detailLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
  },
  detailValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 4,
  },
}); 