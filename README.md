## Basic DNS Resolver ##

Примечания:
- Заменяет CNAME на A записи с минимальным TTL
- Всегда возвращает trace в виде массива, в котором видно, какие выполнялись запросы
- В случае несуществующего адреса возвращает null
- В случае некорректного запроса возвращает код 200 и текст ошибки в теле ответа
- Нет поддержки параллельных запросов (сломается кеш) - можно починить, добавив mutex, но такого требования не было

**Пример запроса:**

```bash
$ curl "http://localhost:8080/get-a-records?domain=ads.adfox.ru&trace=true" -v
*   Trying ::1...
* TCP_NODELAY set
* Connected to localhost (::1) port 8080 (#0)
> GET /get-a-records?domain=ads.adfox.ru&trace=true HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.64.1
> Accept: */*
> 
< HTTP/1.1 200 OK
< Content-Type: application/json; charset=utf-8
< Content-Length: 713
< Date: Thu, 09 Apr 2020 16:51:07 GMT
< Server: Python/3.7 aiohttp/3.6.2
< 
* Connection #0 to host localhost left intact
{"status": "success", "response": [{"request_addr": {"name": "a.root-servers.net.", "address": "198.41.0.4", "ttl": null, "ts": null}, "request_type": "NS", "response": {"name": "a.dns.ripn.net.", "address": "193.232.128.6", "ttl": 172800, "ts": 1586451066}}, {"request_addr": {"name": "a.dns.ripn.net.", "address": "193.232.128.6", "ttl": 172800, "ts": 1586451066}, "request_type": "NS", "response": {"name": "ns2.yandex.RU.", "address": "93.158.134.1", "ttl": 345600, "ts": 1586451067}}, {"request_addr": {"name": "ns2.yandex.RU.", "address": "93.158.134.1", "ttl": 345600, "ts": 1586451067}, "request_type": "A", "response": {"name": "ads.adfox.ru.", "address": "77.88.21.179", "ttl": 300, "ts": 1586451067}}]}* Closing connection 0
```

**Ответ:**

```json
{
  "status": "success",
  "response": [
    {
      "request_addr": {
        "name": "a.root-servers.net.",
        "address": "198.41.0.4",
        "ttl": null,
        "ts": null
      },
      "request_type": "NS",
      "response": {
        "name": "a.dns.ripn.net.",
        "address": "193.232.128.6",
        "ttl": 172800,
        "ts": 1586451066
      }
    },
    {
      "request_addr": {
        "name": "a.dns.ripn.net.",
        "address": "193.232.128.6",
        "ttl": 172800,
        "ts": 1586451066
      },
      "request_type": "NS",
      "response": {
        "name": "ns2.yandex.RU.",
        "address": "93.158.134.1",
        "ttl": 345600,
        "ts": 1586451067
      }
    },
    {
      "request_addr": {
        "name": "ns2.yandex.RU.",
        "address": "93.158.134.1",
        "ttl": 345600,
        "ts": 1586451067
      },
      "request_type": "A",
      "response": {
        "name": "ads.adfox.ru.",
        "address": "77.88.21.179",
        "ttl": 300,
        "ts": 1586451067
      }
    }
  ]
}
```