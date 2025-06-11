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
  const [recordingDuration, setRecordingDuration] = useState(0);
  const scrollViewRef = useRef();
  const durationInterval = useRef();

  // Ses kaydı başlat
  const startRecording = async () => {
    try {
      // Mikrofon izni al
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
      setRecordingDuration(0);
      
      // Süre sayacını başlat
      durationInterval.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
      
      console.log('Ses kaydı başlatıldı');
    } catch (err) {
      console.error('Ses kaydı başlatılamadı:', err);
      Alert.alert('Hata', 'Ses kaydı başlatılamadı');
    }
  };

  // Ses kaydı durdur ve gönder
  const stopRecording = async () => {
    if (!recording) return;

    try {
      setIsRecording(false);
      clearInterval(durationInterval.current);
      
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);
      setRecordingDuration(0);

      console.log('Ses kaydı tamamlandı:', uri);

      if (uri) {
        // Sesli mesajı backend'e gönder
        await sendAudioMessage(uri);
      }
    } catch (error) {
      console.error('Ses kaydı durdurma hatası:', error);
      Alert.alert('Hata', 'Ses kaydı işlenemedi');
    }
  };

  // Sesli mesaj gönder
  const sendAudioMessage = async (audioUri) => {
    // Kullanıcı mesajını ekle (ses ikonu ile)
    const userMessage = {
      id: Date.now(),
      text: '🎤 Sesli mesaj',
      isUser: true,
      isAudio: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Backend'e sesli mesaj gönder
      const response = await apiService.sendAudioMessage(audioUri);
      
      const aiMessage = {
        id: Date.now() + 1,
        text: response.response || 'Üzgünüm, yanıt alamadım.',
        isUser: false,
        timestamp: new Date(),
        originalAudioText: response.original_audio_text,
      };

      setMessages(prev => [...prev, aiMessage]);

      // Eğer ses metni varsa, kullanıcıya göster
      if (response.original_audio_text) {
        // Kullanıcı mesajını güncelle
        setMessages(prev => prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, text: `🎤 "${response.original_audio_text}"` }
            : msg
        ));
      }

      // Yanıtı sesli oku
      Speech.speak(aiMessage.text, {
        language: 'tr-TR',
        pitch: 1.0,
        rate: 0.8,
      });

    } catch (error) {
      console.error('Sesli mesaj gönderme hatası:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Üzgünüm, sesli mesajınızı işleyemedim. Lütfen tekrar deneyin.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
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

  // Mesajı sesli okuma
  const speakMessage = (text) => {
    Speech.speak(text, {
      language: 'tr-TR',
      pitch: 1.0,
      rate: 0.8,
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
            <View style={styles.messageContent}>
              <Text style={[
                styles.messageText,
                message.isUser ? styles.userMessageText : styles.aiMessageText,
              ]}>
                {message.text}
              </Text>
              
              {/* AI mesajları için sesli dinleme butonu */}
              {!message.isUser && (
                <TouchableOpacity
                  style={styles.speakButton}
                  onPress={() => speakMessage(message.text)}
                >
                  <Ionicons name="volume-high" size={16} color="#4A90E2" />
                </TouchableOpacity>
              )}
            </View>
            
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
          style={[styles.voiceButton, isRecording && styles.voiceButtonRecording]}
          onPress={isRecording ? stopRecording : startRecording}
          disabled={isLoading}
        >
          <Ionicons 
            name={isRecording ? 'stop' : 'mic'} 
            size={24} 
            color={isRecording ? '#FFFFFF' : '#4A90E2'} 
          />
          {isRecording && (
            <Text style={styles.recordingDuration}>
              {Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, '0')}
            </Text>
          )}
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
  messageContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  speakButton: {
    marginLeft: 8,
    padding: 4,
    borderRadius: 12,
    backgroundColor: '#F0F8FF',
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
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 50,
  },
  voiceButtonRecording: {
    backgroundColor: '#FF4444',
    paddingHorizontal: 16,
  },
  recordingDuration: {
    color: '#FFFFFF',
    fontSize: 12,
    marginTop: 2,
    fontWeight: 'bold',
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