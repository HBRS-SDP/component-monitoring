from kafka import KafkaConsumer, KafkaProducer

producer = KafkaProducer(bootstrap_servers='localhost:9092')


if __name__ == '__main__':
    #for _ in range(100):
    #    producer.send('foobar', b'some_message_bytes')
    future = producer.send('foobar', b'another_message')
    result = future.get(timeout=60)
    print(result)