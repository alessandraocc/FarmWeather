from secret import secret
from requests import get, post
import time

base_url = 'https://agostinelli-occhionero.appspot.com/'
with open('Farm_Weather_Data.csv', encoding='utf-8-sig') as f:
    for r in f:
        r = r.strip()
        d, maxT, minT, windSpeed, humidity, precipitation = r.split(';')
        maxT = float(maxT)
        minT = float(minT)
        windSpeed = float(windSpeed)
        humidity = float(humidity)
        precipitation = float(precipitation)
        r = post(f'{base_url}/farm/sensor', data={'date': d, 'maxT': maxT, 'minT': minT, 'windSpeed': windSpeed, 'humidity': humidity, 'precipitation': precipitation, 'secret': secret})
        print('sending', d, maxT, minT, windSpeed, humidity, precipitation)
        time.sleep(3)

