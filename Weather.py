
import requests
import json

def weather_forecast(city):
  
    url = 'http://api.openweathermap.org/data/2.5/forecast'
    params = {'q': city, 'units': 'metric', 'APPID': 'f8e0f9b9d9b1f8b1e0b23e7d0f5a5a4b'}
    response = requests.get(url, params=params)
    weather_data = response.json()
    weather_list = weather_data['list']
    for i in weather_list:
        date = i['dt_txt']
        temp = i['main']['temp']
        print(date, ':', temp)
 '''
    import requests
    import json
    url = 'http://api.openweathermap.org/data/2.5/forecast?q={}&units=metric&APPID=d9f8b8f8d0e7c7d6f0e8b8e8e8d9f8b8'
    url = url.format(city)
    response = requests.get(url)
    data = json.loads(response.text)
    weather = data['list']
    for i in weather:
        print('{} {} {}'.format(i['dt_txt'], i['main']['temp'], i['weather'][0]['description']))
'''

print('Enter the city name:')
city = input()
weather_forecast(city)

