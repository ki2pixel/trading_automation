import { isDeepObjectMatch } from '../../src/util/websockets/WsStore';

describe('WsStore', () => {
  describe('isDeepObjectMatch()', () => {
    it('should match two equal strings', () => {
      expect(
        isDeepObjectMatch('orderbook.50.BTCUSDT', 'orderbook.50.BTCUSDT'),
      ).toBeTruthy();
      expect(
        isDeepObjectMatch('orderbook.50.BTCUSDT', 'orderbook.50.ETHUSDT'),
      ).toBeFalsy();
    });

    it('should match simple topic objects', () => {
      const topic1 = {
        topic: 'orderbook.50.BTCUSDT',
      };
      const topic2 = {
        topic: 'orderbook.50.BTCUSDT',
      };

      expect(isDeepObjectMatch(topic1, topic2)).toBeTruthy();
    });

    it('should match topic objects with payload, even if keys are differently ordered', () => {
      const topic1 = {
        topic: 'orderbook.50.BTCUSDT',
        payload: { symbol: 'BTCUSDT' },
        category: 'linear',
      };
      const topic2 = {
        category: 'linear',
        payload: { symbol: 'BTCUSDT' },
        topic: 'orderbook.50.BTCUSDT',
      };

      expect(isDeepObjectMatch(topic1, topic2)).toBeTruthy();
    });

    it('should match nested payload objects', () => {
      const topic1 = {
        topic: 'kline.5.BTCUSDT',
        payload: {
          symbol: 'BTCUSDT',
          interval: '5',
        },
        category: 'spot',
      };
      const topic2 = {
        topic: 'kline.5.BTCUSDT',
        payload: {
          symbol: 'BTCUSDT',
          interval: '5',
        },
        category: 'spot',
      };

      expect(isDeepObjectMatch(topic1, topic2)).toBeTruthy();
    });

    it('should NOT match topics with different category', () => {
      const topic1 = {
        topic: 'orderbook.50.BTCUSDT',
        category: 'linear',
      };
      const topic2 = {
        topic: 'orderbook.50.BTCUSDT',
        category: 'spot',
      };

      expect(isDeepObjectMatch(topic1, topic2)).toBeFalsy();
    });

    it('should NOT match topics with different payload values', () => {
      const topic1 = {
        topic: 'kline.5.BTCUSDT',
        payload: { symbol: 'BTCUSDT' },
        category: 'spot',
      };
      const topic2 = {
        topic: 'kline.5.BTCUSDT',
        payload: { symbol: 'ETHUSDT' },
        category: 'spot',
      };

      expect(isDeepObjectMatch(topic1, topic2)).toBeFalsy();
    });

    it('should NOT match topics with nested payload differences', () => {
      const topic1 = {
        topic: 'kline.5.BTCUSDT',
        payload: {
          symbol: 'BTCUSDT',
          interval: '5',
        },
        category: 'spot',
      };
      const topic2 = {
        topic: 'kline.5.BTCUSDT',
        payload: {
          symbol: 'BTCUSDT',
          interval: '15',
        },
        category: 'spot',
      };

      expect(isDeepObjectMatch(topic1, topic2)).toBeFalsy();
    });

    it('should NOT match asymmetric objects (missing category property)', () => {
      const topic1 = {
        topic: 'orderbook.50.BTCUSDT',
        category: 'linear',
      };
      const topic2 = {
        topic: 'orderbook.50.BTCUSDT',
      };

      expect(isDeepObjectMatch(topic1, topic2)).toBeFalsy();
    });

    it('should NOT match asymmetric objects (missing nested property)', () => {
      const topic1 = {
        topic: 'kline.5.BTCUSDT',
        payload: {
          symbol: 'BTCUSDT',
          interval: '5',
        },
        category: 'spot',
      };
      const topic2 = {
        topic: 'kline.5.BTCUSDT',
        payload: {
          symbol: 'BTCUSDT',
        },
        category: 'spot',
      };

      expect(isDeepObjectMatch(topic1, topic2)).toBeFalsy();
    });

    it('should NOT match string to object', () => {
      expect(
        isDeepObjectMatch('orderbook.50.BTCUSDT', {
          topic: 'orderbook.50.BTCUSDT',
        }),
      ).toBeFalsy();
    });
  });
});
