import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import apiService from '../services/api';

export default function CalendarScreen() {
  const [events, setEvents] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  // Etkinlikleri yükle
  const loadEvents = async () => {
    try {
      const response = await apiService.getCalendarEvents();
      setEvents(response.events || []);
    } catch (error) {
      console.error('Etkinlikler yüklenemedi:', error);
      Alert.alert('Hata', 'Etkinlikler yüklenemedi');
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  // Yenile
  const onRefresh = async () => {
    setRefreshing(true);
    await loadEvents();
    setRefreshing(false);
  };

  // Etkinlik sil
  const deleteEvent = (eventId, eventTitle) => {
    Alert.alert(
      'Etkinlik Sil',
      `"${eventTitle}" etkinliğini silmek istediğinizden emin misiniz?`,
      [
        {
          text: 'İptal',
          style: 'cancel',
        },
        {
          text: 'Sil',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiService.deleteCalendarEvent(eventId);
              Alert.alert('Başarılı', 'Etkinlik silindi');
              loadEvents(); // Listeyi yeniden yükle
            } catch (error) {
              console.error('Etkinlik silinirken hata:', error);
              Alert.alert('Hata', 'Etkinlik silinemedi');
            }
          },
        },
      ]
    );
  };

  // Tarih formatla
  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return {
      time: date.toLocaleTimeString('tr-TR', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      date: date.toLocaleDateString('tr-TR', {
        day: '2-digit',
        month: 'short',
      }),
    };
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.eventsContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {events.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons name="calendar-outline" size={64} color="#CCC" />
            <Text style={styles.emptyText}>Henüz etkinlik yok</Text>
            <Text style={styles.emptySubText}>
              Asistanınızdan yeni etkinlik oluşturmasını isteyin
            </Text>
          </View>
        ) : (
          events.map((event) => {
            const { time, date } = formatDateTime(event.datetime);
            return (
              <View key={event.id} style={styles.eventCard}>
                <View style={styles.timeContainer}>
                  <Text style={styles.timeText}>{time}</Text>
                  <Text style={styles.dateText}>{date}</Text>
                </View>
                
                <View style={styles.eventContent}>
                  <Text style={styles.eventTitle}>{event.title}</Text>
                  {event.description && (
                    <Text style={styles.eventDescription}>
                      {event.description}
                    </Text>
                  )}
                </View>

                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => deleteEvent(event.id, event.title)}
                >
                  <Ionicons name="trash-outline" size={20} color="#FF3B30" />
                </TouchableOpacity>
              </View>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  eventsContainer: {
    flex: 1,
    padding: 16,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginTop: 16,
    fontWeight: '500',
  },
  emptySubText: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
  },
  eventCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  timeContainer: {
    backgroundColor: '#4A90E2',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    minWidth: 70,
  },
  timeText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  dateText: {
    color: 'white',
    fontSize: 12,
    marginTop: 2,
  },
  eventContent: {
    flex: 1,
    marginLeft: 16,
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  eventDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 18,
  },
  deleteButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#FFF0F0',
    marginLeft: 8,
  },
}); 