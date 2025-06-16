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
  SafeAreaView,
  FlatList,
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
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [currentSpeakingMessageId, setCurrentSpeakingMessageId] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const scrollViewRef = useRef();
  const durationInterval = useRef();

  // Sohbet geçmişi için state'ler
  const [showChatHistory, setShowChatHistory] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    {
      id: '1',
      title: 'Toplantı Planlaması',
      lastMessage: 'Tamam, 21 Haziran saat 10:00\'da Erencan ile bir toplantı ekledim...',
      timestamp: '21:37',
      messages: [
        {
          id: '1',
          text: 'Merhaba! Size nasıl yardımcı olabilirim?',
          isUser: false,
          timestamp: new Date(),
        },
        {
          id: '2',
          text: '21 haziran 10.00 toplantı ismi: erencan',
          isUser: true,
          timestamp: new Date(),
        },
        {
          id: '3',
          text: 'Tamam, 21 Haziran saat 10:00\'da "Erencan" başlıklı bir toplantı ekledim takviminize. Başka bir şey eklemek ister misiniz?',
          isUser: false,
          timestamp: new Date(),
        }
      ]
    },
    {
      id: '2',
      title: 'Not Alma',
      lastMessage: 'Tamam, "erencan" başlıklı bir not oluşturdum...',
      timestamp: '21:38',
      messages: [
        {
          id: '1',
          text: 'Merhaba! Size nasıl yardımcı olabilirim?',
          isUser: false,
          timestamp: new Date(),
        },
        {
          id: '2',
          text: 'Not oluştur Başlık : erencan İçerik: erencan seline çok aşık',
          isUser: true,
          timestamp: new Date(),
        },
        {
          id: '3',
          text: 'Tamam, "erencan" başlıklı bir not oluşturdum. İçeriği "erencan seline çok aşık" olarak kaydedildi. Başka bir not oluşturmak veya başka bir şeyde yardımcı olmamı ister misiniz?',
          isUser: false,
          timestamp: new Date(),
        }
      ]
    }
  ]);

  // Yeni sohbet başlat
  const startNewChat = () => {
    if (messages.length <= 1) {
      setMessages([
        {
          id: 1,
          text: 'Merhaba! Size nasıl yardımcı olabilirim?',
          isUser: false,
          timestamp: new Date(),
        },
      ]);
      setInputText('');
      setShowSuggestions(true);
      setIsLoading(false);
      return;
    }

    Alert.alert(
      'Yeni Sohbet',
      'Mevcut sohbeti silip yeni bir sohbet başlatmak istediğinizden emin misiniz?',
      [
        {
          text: 'İptal',
          style: 'cancel',
        },
        {
          text: 'Evet',
          style: 'destructive',
          onPress: () => {
            saveCurrentChatToHistory();
            setMessages([
              {
                id: 1,
                text: 'Merhaba! Size nasıl yardımcı olabilirim?',
                isUser: false,
                timestamp: new Date(),
              },
            ]);
            setInputText('');
            setShowSuggestions(true);
            setIsLoading(false);
          },
        },
      ]
    );
  };

  // Sohbet geçmişini aç/kapat
  const toggleChatHistory = () => {
    setShowChatHistory(!showChatHistory);
  };

  // Geçmişten sohbet yükle
  const loadChatFromHistory = (chatData) => {
    setMessages(chatData.messages);
    setShowChatHistory(false);
    setShowSuggestions(false);
  };

  // Mevcut sohbeti geçmişe kaydet
  const saveCurrentChatToHistory = () => {
    if (messages.length > 1) {
      const newChat = {
        id: Date.now().toString(),
        title: `Sohbet ${new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}`,
        lastMessage: messages[messages.length - 1].text.substring(0, 50) + '...',
        timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
        messages: [...messages]
      };
      setChatHistory(prev => [newChat, ...prev]);
    }
  };

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
      setRecordingDuration(0);
      
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
        await sendAudioMessage(uri);
      }
    } catch (error) {
      console.error('Ses kaydı durdurma hatası:', error);
      Alert.alert('Hata', 'Ses kaydı işlenemedi');
    }
  };

  // Sesli mesaj gönder
  const sendAudioMessage = async (audioUri) => {
    if (showSuggestions) {
      setShowSuggestions(false);
    }

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
      const response = await apiService.sendAudioMessage(audioUri);
      
      const aiMessage = {
        id: Date.now() + 1,
        text: response.response || 'Üzgünüm, yanıt alamadım.',
        isUser: false,
        timestamp: new Date(),
        originalAudioText: response.original_audio_text,
      };

      setMessages(prev => [...prev, aiMessage]);

      if (response.original_audio_text) {
        setMessages(prev => prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, text: `🎤 "${response.original_audio_text}"` }
            : msg
        ));
      }

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

    if (showSuggestions) {
      setShowSuggestions(false);
    }

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
      const response = await apiService.sendMessage(text.trim());
      
      const aiMessage = {
        id: Date.now() + 1,
        text: response.response || 'Üzgünüm, yanıt alamadım.',
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, aiMessage]);

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
  const speakMessage = (text, messageId) => {
    if (currentSpeakingMessageId === messageId && isSpeaking) {
      Speech.stop();
      setCurrentSpeakingMessageId(null);
      setIsSpeaking(false);
      return;
    }

    if (isSpeaking) {
      Speech.stop();
    }

    setCurrentSpeakingMessageId(messageId);
    setIsSpeaking(true);

    Speech.speak(text, {
      language: 'tr-TR',
      pitch: 1.0,
      rate: 0.8,
      onDone: () => {
        setCurrentSpeakingMessageId(null);
        setIsSpeaking(false);
      },
      onStopped: () => {
        setCurrentSpeakingMessageId(null);
        setIsSpeaking(false);
      },
      onError: () => {
        setCurrentSpeakingMessageId(null);
        setIsSpeaking(false);
      },
    });
  };

  return (
    <View style={styles.fullContainer}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.historyButton}
          onPress={toggleChatHistory}
          disabled={isLoading}
        >
          <Ionicons name="time-outline" size={28} color="#007AFF" />
        </TouchableOpacity>
        
        <Text style={styles.headerTitle}>Dijital Asistan</Text>
        
        <TouchableOpacity
          style={styles.newChatButton}
          onPress={startNewChat}
          disabled={isLoading}
        >
          <Ionicons name="add-circle-outline" size={28} color="#007AFF" />
        </TouchableOpacity>
      </View>
      
      <SafeAreaView style={styles.container}>

      {/* Sohbet Geçmişi Paneli */}
      {showChatHistory && (
        <View style={styles.chatHistoryPanel}>
          <View style={styles.chatHistoryHeader}>
            <Text style={styles.chatHistoryTitle}>Sohbet Geçmişi</Text>
            <TouchableOpacity onPress={toggleChatHistory}>
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
          </View>
          
          <FlatList
            data={chatHistory}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.chatHistoryItem}
                onPress={() => loadChatFromHistory(item)}
              >
                <View style={styles.chatHistoryItemContent}>
                  <Text style={styles.chatHistoryItemTitle}>{item.title}</Text>
                  <Text style={styles.chatHistoryItemMessage}>{item.lastMessage}</Text>
                </View>
                <Text style={styles.chatHistoryItemTime}>{item.timestamp}</Text>
              </TouchableOpacity>
            )}
            style={styles.chatHistoryList}
          />
        </View>
      )}

      <KeyboardAvoidingView 
        style={styles.keyboardAvoidingView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        {/* Mesajlar */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          onContentSizeChange={() => scrollViewRef.current?.scrollToEnd()}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ paddingBottom: 20 }}
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
                    style={[
                      styles.speakButton,
                      currentSpeakingMessageId === message.id && isSpeaking && styles.speakButtonActive
                    ]}
                    onPress={() => speakMessage(message.text, message.id)}
                  >
                    <Ionicons 
                      name={currentSpeakingMessageId === message.id && isSpeaking ? "stop" : "volume-high"} 
                      size={16} 
                      color={currentSpeakingMessageId === message.id && isSpeaking ? "#FF6B6B" : "#4A90E2"} 
                    />
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
        {showSuggestions && (
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
            autoCorrect={false}
            autoCapitalize="none"
            spellCheck={false}
            autoComplete="off"
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
    </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  fullContainer: {
    flex: 1,
    backgroundColor: '#007AFF',
  },
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  header: {
    backgroundColor: '#007AFF',
    paddingTop: 50,
    paddingBottom: 15,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    flex: 1,
    textAlign: 'center',
  },
  newChatButton: {
    padding: 10,
    borderRadius: 25,
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#007AFF',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  historyButton: {
    padding: 10,
    borderRadius: 25,
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#007AFF',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  chatHistoryPanel: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 1000,
  },
  chatHistoryHeader: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 15,
    paddingHorizontal: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    marginTop: 100,
  },
  chatHistoryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  chatHistoryList: {
    backgroundColor: '#FFFFFF',
    flex: 1,
  },
  chatHistoryItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  chatHistoryItemContent: {
    flex: 1,
    marginRight: 10,
  },
  chatHistoryItemTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  chatHistoryItemMessage: {
    fontSize: 14,
    color: '#666',
    numberOfLines: 1,
  },
  chatHistoryItemTime: {
    fontSize: 12,
    color: '#999',
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
  speakButtonActive: {
    backgroundColor: '#FFE5E5',
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