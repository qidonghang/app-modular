"""
config.py
---------
Default settings for the app.

Edit the values below to pre-fill fields every time the app opens.
"""

# ── Google Sheets URLs ────────────────────────────────────────────────────────
# Paste your Google Sheets URLs here (between the quotes).
# These pre-fill the Brand Judge / Brand Auth fields in the UI.
BRAND_JUDGE_URL = "https://docs.google.com/spreadsheets/d/1Z_TnKzcp7Oe7cTIUSbIO0P0uZrWs0NnuWCIR1Wnv_5M/edit?gid=1315256570#gid=1315256570"
BRAND_AUTH_URL  = "https://docs.google.com/spreadsheets/d/1Z_TnKzcp7Oe7cTIUSbIO0P0uZrWs0NnuWCIR1Wnv_5M/edit?gid=1305099045#gid=1305099045"

# ── Google Service Account Key (embedded) ────────────────────────────────────
# The service account credentials are embedded directly so the EXE works
# without needing an external JSON file next to it.
SERVICE_ACCOUNT_KEY = {
    "type": "service_account",
    "project_id": "joey-chen",
    "private_key_id": "e28fd25614393452ccfc1faaa011584bda025c88",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCXg0hQAB6JTW+d\nyigDxt0V7SHwdRQglwv9wzjZVNvRZVHKvk7x2OiNZgEOYksk4gYdnPNZCZA88j+7\nqgK6RswgSYUUzuWxIBvEM+SoaDVYEcdKat8r6YW951GbqjWDhDbg0ZBBmi5LOFu9\nJYTQ0iIv0TP4e1wcmCI5AoQJbgX3YlXHUorUW8JZkh8Vk+F4pspXjgo9lro3QfPB\nMROigcINoqDpsJSu2Vs6vlUOoiEbaoGlEV0DWfAoRrzdtgzdRRzF7AQMAbdK58P2\nzG4UeJVp99PusFIn4/SgeZUNGb/EDG2axJBYSU8jRmCZy24vl2zdpBxfeCHOSWxY\nYdZBzs+JAgMBAAECggEAROBU4K1VNGSj3261ZxYhjiSpH5cRqckQlfEH6GB3t0ag\nepKt76qD+TeMNl4/u8oWLqMZSvoafGJBz813BPhHNkxFt9JgP3eRt81BXr9UtK8M\nUkuoHV3AwzYjdqjXP+y8R9Jsii4Nant51M/4Azfre6JWRljJ5GPSdukqXeEKzEzP\n33sieF+S3ElhQroX/50mFT8yTgZ3o/nbacsIk5SByfbwQ+2KUPQBPu4ngkHHpakE\nQKymNHl4A/X9CyE75NEbQ1pmj/2zXmmO3R21W0J6kHtgAWV8nRKs8Yr79lGcRqrt\nR9MBvAOGjbNaT68K/82o/tZliUllcNOBfYzneBv9SwKBgQDOhUedLo2Cq5TiPGgw\nC1tUw86nZRUlUjSjyOeXnMAy/g+jDuh6REQaz7D9YfwZV0VsLTrnOifmylC2PKiq\nUltVZfkM+KnNg/XCoQ8mw0A2LFKC6zp3iRA5B7eqJ9FBcxPsTZHpXPT4r3d5AowM\nIk7/SEc6eYvZXojeObC4HSkfbwKBgQC70CiMSYpa9EwmIeauwLdkLpY8I0CX1X2S\n0xkXU8GXDE18r1waV+ZK5/zNSv90weIwnp89Xnnhe/vwC9qLrhiludLfM5TKM7jH\ngQzzcYwv+OrDaByfUAiBUHv+btgagBVHRb7WpUmvt2U7D4WUfiSrxgvLJsk7KcBs\nbVrx7LaEhwKBgFcIfhS0wLhX3Qe202Wj85p2ZonPJKk0yrBXg5o2Wh1jSm26Y6jb\nSiROcNVnzNlVGRGswg0eSiCOFJOoXqBg0tLbhai8xrqwqQqb24nHcTEjXqaDwYEM\nx0RxhypzW1GM0NGeIybIoQiI0f2yYBjhAI+/Ax2WiaRSnbWhdGMzDtiLAoGAJek9\n1hueJv/7QxNCynGyUzGoN9lx13RL1dBw1ymcAU6Fca7AK70kimhLunDyIfJlIyVR\nxYSFm8N4Nptd8SYiaYmaDF4QIcTQ/syI/bck8iYP1YP1ix8PqHLDpLdhPfAu22Uz\nwYY52pNthr96WmAgLOBcTxS0OBIUeo6UdhMvQI8CgYB1xt3sXECsxck1A5QXKsii\nFoRboaNJajWTuvAKO4p7B142l6LroxpQ6dnv6ykGScZUc4faTHDYh4JZ0q7/+T8B\nHhw7PTQRg7GxNGsEo48TgXu4irEwMgjO1tTiMHqChrvG+k56kfvTQ6Smmw6agEbn\n8sDobqfi4p0UlLYedQkRYw==\n-----END PRIVATE KEY-----\n",
    "client_email": "joey-chen@joey-chen.iam.gserviceaccount.com",
    "client_id": "111417666961463787318",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/joey-chen%40joey-chen.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}
