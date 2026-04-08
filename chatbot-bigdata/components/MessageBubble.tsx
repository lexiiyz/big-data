import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/theme';
import { Message } from '@/types/chat';
import { useColorScheme } from '@/hooks/use-color-scheme';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const colorScheme = useColorScheme() ?? 'light';
  const theme = Colors[colorScheme];
  const isUser = message.isUser;

  return (
    <View style={[
      styles.messageWrapper,
      isUser ? styles.messageWrapperUser : styles.messageWrapperBot
    ]}>
      {!isUser && (
        <View style={[styles.avatar, { backgroundColor: theme.tint }]}>
          <Ionicons name="server" size={16} color="#FFF" />
        </View>
      )}
      <View style={[
        styles.messageBubble,
        isUser 
          ? { backgroundColor: theme.messageUserBg, borderBottomRightRadius: 4 }
          : { backgroundColor: theme.messageBotBg, borderBottomLeftRadius: 4 }
      ]}>
        <Text style={[
          styles.messageText,
          isUser ? { color: theme.messageUserText } : { color: theme.messageBotText }
        ]}>
          {message.text}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  messageWrapper: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-end',
  },
  messageWrapperUser: {
    justifyContent: 'flex-end',
  },
  messageWrapperBot: {
    justifyContent: 'flex-start',
  },
  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
    marginBottom: 4,
  },
  messageBubble: {
    maxWidth: '80%',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 18,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
});
