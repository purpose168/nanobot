/**
 * 用于 Python-Node.js 桥接通信的 WebSocket 服务器。
 */

import { WebSocketServer, WebSocket } from 'ws';
import { WhatsAppClient, InboundMessage } from './whatsapp.js';

interface SendCommand {
  type: 'send';
  to: string;
  text: string;
}

interface BridgeMessage {
  type: 'message' | 'status' | 'qr' | 'error';
  [key: string]: unknown;
}

export class BridgeServer {
  private wss: WebSocketServer | null = null;
  private wa: WhatsAppClient | null = null;
  private clients: Set<WebSocket> = new Set();

  constructor(private port: number, private authDir: string) {}

  async start(): Promise<void> {
    // 创建 WebSocket 服务器
    this.wss = new WebSocketServer({ port: this.port });
    console.log(`🌉 桥接服务器监听 ws://localhost:${this.port}`);

    // 初始化 WhatsApp 客户端
    this.wa = new WhatsAppClient({
      authDir: this.authDir,
      onMessage: (msg) => this.broadcast({ type: 'message', ...msg }),
      onQR: (qr) => this.broadcast({ type: 'qr', qr }),
      onStatus: (status) => this.broadcast({ type: 'status', status }),
    });

    // 处理 WebSocket 连接
    this.wss.on('connection', (ws) => {
      console.log('🔗 Python 客户端已连接');
      this.clients.add(ws);

      ws.on('message', async (data) => {
        try {
          const cmd = JSON.parse(data.toString()) as SendCommand;
          await this.handleCommand(cmd);
          ws.send(JSON.stringify({ type: 'sent', to: cmd.to }));
        } catch (error) {
          console.error('处理命令时出错:', error);
          ws.send(JSON.stringify({ type: 'error', error: String(error) }));
        }
      });

      ws.on('close', () => {
        console.log('🔌 Python 客户端已断开');
        this.clients.delete(ws);
      });

      ws.on('error', (error) => {
        console.error('WebSocket 错误:', error);
        this.clients.delete(ws);
      });
    });

    // 连接到 WhatsApp
    await this.wa.connect();
  }

  private async handleCommand(cmd: SendCommand): Promise<void> {
    if (cmd.type === 'send' && this.wa) {
      await this.wa.sendMessage(cmd.to, cmd.text);
    }
  }

  private broadcast(msg: BridgeMessage): void {
    const data = JSON.stringify(msg);
    for (const client of this.clients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(data);
      }
    }
  }

  async stop(): Promise<void> {
    // 关闭所有客户端连接
    for (const client of this.clients) {
      client.close();
    }
    this.clients.clear();

    // 关闭 WebSocket 服务器
    if (this.wss) {
      this.wss.close();
      this.wss = null;
    }

    // 断开 WhatsApp 连接
    if (this.wa) {
      await this.wa.disconnect();
      this.wa = null;
    }
  }
}
