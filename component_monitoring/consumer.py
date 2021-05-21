#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 21.05.21 23:21
# @Author  : Vincent Scharf
# @File    : consumer.py

from kafka import KafkaConsumer

if __name__ == "__main__":
    consumer = KafkaConsumer('foobar')

    for msg in consumer:
        print(msg)