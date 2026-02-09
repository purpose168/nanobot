#!/usr/bin/env node
/**
 * nanobot WhatsApp 桥接
 * 
 * 此桥接通过 WebSocket 将 WhatsApp Web 连接到 nanobot 的 Python 后端。
 * 它处理身份验证、消息转发和重新连接逻辑。
 * 
 * 使用方法：
 *   npm run build && npm start
 *   
 * 或使用自定义设置：
 *   BRIDGE_PORT=3001 AUTH_DIR=~/.nanobot/whatsapp npm start
 */

// 为 ESM 中的 Baileys 填充 crypto
import { webcrypto } from 'crypto';
if (!globalThis.crypto) {
  (globalThis as any).crypto = webcrypto;
}

import { BridgeServer } from './server.js';
import { homedir } from 'os';
import { join } from 'path';

const PORT = parseInt(process.env.BRIDGE_PORT || '3001', 10);
const AUTH_DIR = process.env.AUTH_DIR || join(homedir(), '.nanobot', 'whatsapp-auth');

console.log('🐈 nanobot WhatsApp 桥接');
console.log('========================\n');

const server = new BridgeServer(PORT, AUTH_DIR);

// 处理优雅关闭
process.on('SIGINT', async () => {
  console.log('\n\n正在关闭...');
  await server.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await server.stop();
  process.exit(0);
});

// 启动服务器
server.start().catch((error) => {
  console.error('启动桥接失败:', error);
  process.exit(1);
});
