import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert,
  Platform,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { KeyboardAwareScrollView } from 'react-native-keyboard-aware-scroll-view';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import { sendMessage, sendAudioMessage } from '../services/api';

export default function ChatScreen() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [recording, setRecording] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const flatListRef = useRef(null);

  // Hızlı öneriler
  const quickSuggestions = [
    'Bugün hava nasıl?',
    'Yeni bir not oluştur',
    'Yarın toplantım var mı?',
    'Hatırlatıcı kur',
  ];

  useEffect(() => {
    // İlk mesaj
    setMessages([
      {
        id: '1',
        text: 'Merhaba! Size nasıl yardımcı olabilirim?',
        isUser: false,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const scrollToBottom = () => {
    if (flatListRef.current && messages.length > 0) {
      setTimeout(() => {
        flatListRef.current.scrollToEnd({ animated: true });
      }, 100);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (messageText = inputText) => {
    if (!messageText.trim() || isLoading) return;

    // İlk mesaj gönderildiğinde önerileri gizle
    if (showSuggestions) {
      setShowSuggestions(false);
    }

    const userMessage = {
      id: Date.now().toString(),
      text: messageText.trim(),
      isUser: true,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      console.log('Sending message:', messageText.trim());
      const response = await sendMessage(messageText.trim());
      console.log('Response received:', response);

      const botMessage = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        isUser: false,
        timestamp: response.timestamp,
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Mesaj gönderme hatası:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.',
        isUser: false,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickSuggestion = (suggestion) => {
    handleSendMessage(suggestion);
  };

  const startRecording = async () => {
    try {
      console.log('Ses kaydı izni isteniyor...');
      const permission = await Audio.requestPermissionsAsync();
      
      if (permission.status !== 'granted') {
        Alert.alert('İzin Gerekli', 'Ses kaydı için mikrofon izni gereklidir.');
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      console.log('Ses kaydı başlatılıyor...');
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      
      setRecording(recording);
      setIsRecording(true);
      console.log('Ses kaydı başlatıldı');
    } catch (err) {
      console.error('Ses kaydı başlatılamadı:', err);
      Alert.alert('Hata', 'Ses kaydı başlatılamadı.');
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      console.log('Ses kaydı durduruluyor...');
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      
      const uri = recording.getURI();
      console.log('Ses kaydı tamamlandı:', uri);
      
      setRecording(null);
      
      if (uri) {
        await sendAudioMessageToAPI(uri);
      }
    } catch (error) {
      console.error('Ses kaydı durdurulurken hata:', error);
      Alert.alert('Hata', 'Ses kaydı kaydedilemedi.');
    }
  };

  const sendAudioMessageToAPI = async (audioUri) => {
    setIsLoading(true);
    
    // İlk mesaj gönderildiğinde önerileri gizle
    if (showSuggestions) {
      setShowSuggestions(false);
    }
    
    try {
      console.log('Sending audio message:', audioUri);
      const response = await sendAudioMessage(audioUri);
      console.log('Audio response received:', response);

      // Kullanıcının ses mesajını ekle
      const userMessage = {
        id: Date.now().toString(),
        text: `🎤 Sesli mesaj: "${response.original_audio_text}"`,
        isUser: true,
        timestamp: response.timestamp,
      };

      // Bot cevabını ekle
      const botMessage = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        isUser: false,
        timestamp: response.timestamp,
      };

      setMessages(prev => [...prev, userMessage, botMessage]);
    } catch (error) {
      console.error('Sesli mesaj gönderme hatası:', error);
      Alert.alert('Hata', 'Sesli mesaj gönderilemedi.');
    } finally {
      setIsLoading(false);
    }
  };

  const speakText = (text) => {
    Speech.speak(text, {
      language: 'tr-TR',
      pitch: 1.0,
      rate: 0.8,
    });
  };

  const renderMessage = ({ item }) => (
    <View style={[
      styles.messageContainer,
      item.isUser ? styles.userMessage : styles.botMessage
    ]}>
      <View style={[
        styles.messageBubble,
        item.isUser ? styles.userBubble : styles.botBubble
      ]}>
        <Text style={[
          styles.messageText,
          item.isUser ? styles.userText : styles.botText
        ]}>
          {item.text}
        </Text>
      </View>
      {!item.isUser && (
        <TouchableOpacity
          style={styles.speakButton}
          onPress={() => speakText(item.text)}
        >
          <Ionicons name="volume-high" size={20} color="#007AFF" />
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI Asistan</Text>
      </View>
      
      <KeyboardAwareScrollView
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
        enableOnAndroid={true}
        enableAutomaticScroll={true}
        extraScrollHeight={100}
        keyboardOpeningTime={0}
        showsVerticalScrollIndicator={false}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          style={styles.messagesList}
          contentContainerStyle={styles.messagesListContent}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={scrollToBottom}
          onLayout={scrollToBottom}
          scrollEnabled={false}
        />
      </KeyboardAwareScrollView>

      {/* Alt Kısım - Öneriler ve Input */}
      <View style={styles.bottomContainer}>
        {/* Hızlı Öneriler - Sadece ilk mesajdan önce göster */}
        {showSuggestions && (
          <View style={styles.suggestionsContainer}>
            <ScrollView 
              horizontal 
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.suggestionsContent}
            >
              {quickSuggestions.map((suggestion, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.suggestionButton}
                  onPress={() => handleQuickSuggestion(suggestion)}
                  disabled={isLoading}
                >
                  <Text style={styles.suggestionText}>{suggestion}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Mesaj Girişi */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Mesajınızı yazın..."
            multiline
            maxLength={500}
            editable={!isLoading}
          />
          
          <TouchableOpacity
            style={[styles.recordButton, isRecording && styles.recordingButton]}
            onPress={isRecording ? stopRecording : startRecording}
            disabled={isLoading}
          >
            <Ionicons 
              name={isRecording ? "stop" : "mic"} 
              size={24} 
              color={isRecording ? "#FF3B30" : "#007AFF"} 
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.sendButton, (!inputText.trim() || isLoading) && styles.disabledButton]}
            onPress={() => handleSendMessage()}
            disabled={!inputText.trim() || isLoading}
          >
            <Ionicons name="send" size={24} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    flexGrow: 1,
  },
  messagesList: {
    flex: 1,
  },
  messagesListContent: {
    paddingVertical: 10,
    paddingHorizontal: 15,
    paddingBottom: 20,
  },
  messageContainer: {
    marginVertical: 5,
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  userMessage: {
    justifyContent: 'flex-end',
  },
  botMessage: {
    justifyContent: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderRadius: 20,
    marginHorizontal: 5,
  },
  userBubble: {
    backgroundColor: '#007AFF',
    borderBottomRightRadius: 5,
  },
  botBubble: {
    backgroundColor: '#FFFFFF',
    borderBottomLeftRadius: 5,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#FFFFFF',
  },
  botText: {
    color: '#333333',
  },
  speakButton: {
    padding: 5,
    marginLeft: 5,
  },
  bottomContainer: {
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  suggestionsContainer: {
    paddingVertical: 6,
    paddingHorizontal: 15,
  },
  suggestionsContent: {
    paddingRight: 10,
  },
  suggestionButton: {
    backgroundColor: '#F0F8FF',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginRight: 6,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  suggestionText: {
    color: '#007AFF',
    fontSize: 11,
    fontWeight: '500',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 15,
    paddingVertical: 10,
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 25,
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 16,
    maxHeight: 100,
    backgroundColor: '#F8F8F8',
    marginRight: 10,
  },
  recordButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#F0F0F0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  recordingButton: {
    backgroundColor: '#FFE5E5',
  },
  sendButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#CCCCCC',
  },

}); 