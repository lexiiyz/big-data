/**
 * Below are the colors that are used in the app. The colors are defined in the light and dark mode.
 * There are many other ways to style your app. For example, [Nativewind](https://www.nativewind.dev/), [Tamagui](https://tamagui.dev/), [unistyles](https://reactnativeunistyles.vercel.app), etc.
 */

import { Platform } from 'react-native';

const tintColorLight = '#0a7ea4';
const tintColorDark = '#fff';

export const Colors = {
  light: {
    text: '#11181C',
    background: '#F4F5F7',
    tint: '#1D63ED',
    icon: '#687076',
    tabIconDefault: '#687076',
    tabIconSelected: '#1D63ED',
    messageUserText: '#FFFFFF',
    messageBotText: '#11181C',
    messageUserBg: '#1D63ED',
    messageBotBg: '#E2E6EC',
    inputBg: '#FFFFFF',
    inputText: '#11181C',
    borderColor: '#D3DAE6'
  },
  dark: {
    text: '#FFFFFF',
    background: '#1D2025',
    tint: '#1D63ED',
    icon: '#9BA1A6',
    tabIconDefault: '#9BA1A6',
    tabIconSelected: '#1D63ED',
    messageUserText: '#FFFFFF',
    messageBotText: '#FFFFFF',
    messageUserBg: '#1D63ED',
    messageBotBg: '#2D323A',
    inputBg: '#2D323A',
    inputText: '#FFFFFF',
    borderColor: '#3D4551'
  },
};

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    serif: "Georgia, 'Times New Roman', serif",
    rounded: "'SF Pro Rounded', 'Hiragino Maru Gothic ProN', Meiryo, 'MS PGothic', sans-serif",
    mono: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  },
});
