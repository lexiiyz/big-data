import React from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

interface ChatInputProps {
  value: string;
  onChangeText: (text: string) => void;
  onSend: () => void;
  isLoading: boolean;
}

export function ChatInput({ value, onChangeText, onSend, isLoading }: ChatInputProps) {
  const colorScheme = useColorScheme() ?? 'light';
  const theme = Colors[colorScheme];

  const hasText = value.trim().length > 0;

  return (
    <View style={[styles.inputContainer, { 
      backgroundColor: theme.inputBg, 
      borderTopColor: theme.borderColor 
    }]}>
      <TextInput
        style={[styles.input, { 
          color: theme.inputText,
          backgroundColor: theme.background,
          borderColor: theme.borderColor
        }]}
        placeholder="Ask BigData something..."
        placeholderTextColor={theme.icon}
        value={value}
        onChangeText={onChangeText}
        multiline
        maxLength={500}
      />
      <TouchableOpacity 
         style={[styles.sendButton, { 
           backgroundColor: hasText ? theme.tint : theme.borderColor 
         }]}
         onPress={onSend}
         disabled={isLoading || !hasText}
      >
        <Ionicons name="send" size={16} color="#FFF" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    paddingBottom: Platform.OS === 'ios' ? 24 : 12,
    borderTopWidth: 1,
    alignItems: 'center',
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    borderWidth: 1,
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 12,
    fontSize: 16,
    marginRight: 10,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
