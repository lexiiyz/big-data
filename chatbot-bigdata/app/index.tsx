import React, { useState, useRef, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  ActivityIndicator,
  useColorScheme
} from 'react-native';
import { Colors } from '@/constants/theme';
import { useHeaderHeight } from '@react-navigation/elements';
import { Message } from '@/types/chat';
import { sendChatMessage } from '@/services/chatService';
import { MessageBubble } from '@/components/MessageBubble';
import { ChatInput } from '@/components/ChatInput';

export default function ChatScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const theme = Colors[colorScheme];
  const headerHeight = useHeaderHeight();

  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: 'Hello! I am your BigData Assistant. How can I help you today?', isUser: false }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (messages.length > 0) {
        setTimeout(() => {
            flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);
    }
  }, [messages]);

  useEffect(() => {
    const showSub = Keyboard.addListener('keyboardDidShow', () => {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    });
    return () => showSub.remove();
  }, []);

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      isUser: true,
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const botResponseText = await sendChatMessage(userMsg.text);

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: botResponseText,
        isUser: false,
      };

      setMessages(prev => [...prev, botMsg]);

    } catch (error: any) {
      console.error('Error calling n8n webhook:', error);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: `Network Error: Could not connect to the n8n webhook. Make sure the n8n webhook is active and CORS is handled.\nDetails: ${error.message}`,
        isUser: false,
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={[styles.container, { backgroundColor: theme.background }]} 
      behavior="padding"
      keyboardVerticalOffset={headerHeight}
    >
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={item => item.id}
        renderItem={({ item }) => <MessageBubble message={item} />}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
      
      {isLoading && (
        <View style={styles.loadingContainer}>
            <Text style={{ color: theme.icon, marginRight: 8, fontSize: 13 }}>Bot is thinking...</Text>
            <ActivityIndicator size="small" color={theme.tint} />
        </View>
      )}

      <ChatInput 
        value={inputText}
        onChangeText={setInputText}
        onSend={handleSend}
        isLoading={isLoading}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  listContent: {
    padding: 16,
    paddingBottom: 24,
  },
  loadingContainer: {
     flexDirection: 'row',
     paddingHorizontal: 24,
     paddingBottom: 16,
     alignItems: 'center',
  },
});
