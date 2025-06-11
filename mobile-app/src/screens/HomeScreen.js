import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import apiService from '../services/api';

export default function HomeScreen() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: 'Merhaba! Size nasıl yardımcı olabilirim?',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recording, setRecording] = useState(null);
  const scrollViewRef = useRef();

  // Ses kaydı başlat
  const startRecording = async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Hata', 'Mikrofon izni gerekli');
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
      );
      setRecording(recording);
      setIsRecording(true);
    } catch (err) {
      console.error('Ses kaydı başlatılamadı:', err);
      Alert.alert('Hata', 'Ses kaydı başlatılamadı');
    }
  };

  // Ses kaydı durdur
  const stopRecording = async () => {
    if (!recording) return;

    setIsRecording(false);
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();
    setRecording(null);

    // Ses dosyasını metne çevir (şimdilik placeholder)
    // Gerçek uygulamada speech-to-text servisi kullanılacak
    Alert.alert('Bilgi', 'Ses kaydı tamamlandı. Şimdilik metin girişi kullanın.');
  };

  // Mesaj gönder
  const sendMessage = async (text = inputText) => {
    if (!text.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: text.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Backend'e mesaj gönder
      const response = await apiService.sendMessage(text.trim());
      
      const aiMessage = {
        id: Date.now() + 1,
        text: response.response || 'Üzgünüm, yanıt alamadım.',
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, aiMessage]);

      // Yanıtı sesli oku
      Speech.speak(aiMessage.text, {
        language: 'tr-TR',
        pitch: 1.0,
        rate: 0.8,
      });

    } catch (error) {
      console.error('Mesaj gönderme hatası:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Üzgünüm, şu anda yanıt veremiyorum. Lütfen tekrar deneyin.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Hızlı komutlar
  const quickCommands = [
    'Yarın saat 10:00\'da toplantı var mı?',
    'Bugün hava nasıl?',
    'Yeni bir not oluştur',
    'Hatırlatıcılarımı göster',
  ];

  const handleQuickCommand = (command) => {
    sendMessage(command);
  };

  // Mesaj formatla
  const formatTime = (date) => {
    return date.toLocaleTimeString('tr-TR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Mesajlar */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        onContentSizeChange={() => scrollViewRef.current?.scrollToEnd()}
      >
        {messages.map((message) => (
          <View
            key={message.id}
            style={[
              styles.messageContainer,
              message.isUser ? styles.userMessage : styles.aiMessage,
            ]}
          >
            <Text style={[
              styles.messageText,
              message.isUser ? styles.userMessageText : styles.aiMessageText,
            ]}>
              {message.text}
            </Text>
            <Text style={[
              styles.messageTime,
              message.isUser ? styles.userMessageTime : styles.aiMessageTime,
            ]}>
              {formatTime(message.timestamp)}
            </Text>
          </View>
        ))}
        
        {isLoading && (
          <View style={[styles.messageContainer, styles.aiMessage]}>
            <Text style={styles.loadingText}>Yanıt yazıyor...</Text>
          </View>
        )}
      </ScrollView>

      {/* Hızlı Komutlar */}
      <ScrollView 
        horizontal 
        style={styles.quickCommandsContainer}
        showsHorizontalScrollIndicator={false}
      >
        {quickCommands.map((command, index) => (
          <TouchableOpacity
            key={index}
            style={styles.quickCommandButton}
            onPress={() => handleQuickCommand(command)}
          >
            <Text style={styles.quickCommandText}>{command}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Mesaj Girişi */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Mesajınızı yazın..."
          multiline
          maxLength={500}
        />
        
        <TouchableOpacity
          style={styles.voiceButton}
          onPress={isRecording ? stopRecording : startRecording}
        >
          <Ionicons 
            name={isRecording ? 'stop' : 'mic'} 
            size={24} 
            color={isRecording ? '#FF4444' : '#4A90E2'} 
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
          onPress={() => sendMessage()}
          disabled={!inputText.trim() || isLoading}
        >
          <Ionicons name="send" size={20} color="white" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  messagesContainer: {
    flex: 1,
    padding: 16,
  },
  messageContainer: {
    marginVertical: 4,
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#4A90E2',
  },
  aiMessage: {
    alignSelf: 'flex-start',
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#E5E5E5',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  userMessageText: {
    color: 'white',
  },
  aiMessageText: {
    color: '#333',
  },
  messageTime: {
    fontSize: 12,
    marginTop: 4,
  },
  userMessageTime: {
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'right',
  },
  aiMessageTime: {
    color: '#999',
  },
  loadingText: {
    color: '#999',
    fontStyle: 'italic',
  },
  quickCommandsContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  quickCommandButton: {
    backgroundColor: 'white',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#4A90E2',
  },
  quickCommandText: {
    color: '#4A90E2',
    fontSize: 14,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: 'white',
    alignItems: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: '#E5E5E5',
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E5E5',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    maxHeight: 100,
    fontSize: 16,
  },
  voiceButton: {
    marginLeft: 8,
    padding: 12,
    borderRadius: 25,
    backgroundColor: '#F0F0F0',
  },
  sendButton: {
    marginLeft: 8,
    padding: 12,
    borderRadius: 25,
    backgroundColor: '#4A90E2',
  },
  sendButtonDisabled: {
    backgroundColor: '#CCC',
  },
}); 