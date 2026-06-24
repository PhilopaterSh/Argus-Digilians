from app.core.brain import ArgusBrain

if __name__ == '__main__':
    b = ArgusBrain('WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest', [])
    print('Calling simple_ask...')
    resp = b.simple_ask('Say hello and indicate readiness')
    print('RESPONSE:\n', resp)
