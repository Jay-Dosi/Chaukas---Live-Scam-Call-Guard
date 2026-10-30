import type {
  ClientMessage,
  ServerEvent,
  Level,
  Analysis,
} from '@protocol/index';

export type { Level, Analysis, ClientMessage, ServerEvent };

type MessageHandler = (event: ServerEvent) => void;
type ErrorHandler = (error: Error) => void;
type MessageType = ServerEvent['type'] | 'closed' | string;

export class SessionSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<MessageType, Set<MessageHandler>> = new Map();
  private errorHandlers: Set<ErrorHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 1000;
  private closed = false;
  private sendQueue: string[] = [];

  constructor(baseUrl?: string) {
    this.url = baseUrl ?? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/session`;
  }

  connect() {
    if (this.ws && this.ws.readyState <= WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(this.url);
    } catch {
      this.emitError(new Error('WebSocket connection failed'));
      return;
    }

    this.ws.onopen = () => {
      this.closed = false;
      this.reconnectAttempts = 0;
      while (this.sendQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
        const item = this.sendQueue.shift();
        if (item) {
          try {
            this.ws.send(item);
          } catch (e) {
            console.error('Failed to flush message in queue:', e);
          }
        }
      }
    };

    this.ws.onmessage = (event) => {
      let data: ServerEvent;
      try {
        data = JSON.parse(event.data);
      } catch {
        this.emitError(new Error(`Invalid WS message: ${event.data}`));
        return;
      }
      this.dispatch(data);
    };

    this.ws.onclose = () => {
      this.closed = true;
      this.tryReconnect();
    };

    this.ws.onerror = () => {
      this.emitError(new Error('WebSocket error'));
    };
  }

  private dispatch(event: ServerEvent) {
    const handlers = this.handlers.get(event.type);
    if (handlers) {
      handlers.forEach((fn) => fn(event));
    }
    // Also call the wildcard handler
    const allHandlers = this.handlers.get('*');
    if (allHandlers) {
      allHandlers.forEach((fn) => fn(event));
    }
  }

  on<T extends ServerEvent['type']>(
    type: T,
    handler: (event: Extract<ServerEvent, { type: T }>) => void,
  ): () => boolean;
  on(type: string, handler: (event: any) => void): () => boolean;
  on(type: string, handler: (event: any) => void) {
    const existing = this.handlers.get(type) ?? new Set();
    existing.add(handler);
    this.handlers.set(type, existing);
    return () => existing.delete(handler);
  }

  onError(handler: ErrorHandler) {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  private emitError(error: Error) {
    this.errorHandlers.forEach((fn) => fn(error));
  }

  send(message: ClientMessage) {
    const payload = JSON.stringify(message);
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(payload);
      } catch (err) {
        this.sendQueue.push(payload);
        this.emitError(new Error(`WebSocket send error: ${err}`));
      }
    } else {
      this.sendQueue.push(payload);
      if (!this.ws || this.ws.readyState > WebSocket.OPEN) {
        this.connect();
      }
    }
  }

  sendBinary(data: ArrayBuffer | ArrayBufferView) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(data);
      } catch {
        // Drop frames gracefully on backpressure
      }
    }
  }

  close() {
    this.closed = true;
    this.reconnectAttempts = 0;
    this.ws?.close();
  }

  private tryReconnect() {
    if (this.closed) return;
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.emitError(new Error('Max reconnection attempts reached'));
      return;
    }
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    setTimeout(() => this.connect(), delay);
  }

  isOpen(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Utility functions for the Live Guard flow
export function startSession(socket: SessionSocket, params: {
  mode: 'live' | 'inject' | 'upload' | 'drill';
  lang: 'hi-IN' | 'en-IN' | 'auto';
  sensitivity: 'standard' | 'high';
  scenario_id?: string;
  fixture_id?: string;
}) {
  socket.send({
    type: 'start',
    mode: params.mode,
    lang: params.lang,
    sensitivity: params.sensitivity,
    sample_rate: 16000,
    scenario_id: params.scenario_id,
    fixture_id: params.fixture_id,
  });
}

export function stopSession(socket: SessionSocket) {
  socket.send({ type: 'stop' });
}

export function muteForAlert(socket: SessionSocket, ms: number) {
  socket.send({ type: 'mute', ms });
}
