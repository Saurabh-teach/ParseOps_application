with open('c:/Users/saura/ParseOps/backend/config/settings.py', 'a', encoding='utf-8') as f:
    f.write('\nASGI_APPLICATION = "config.asgi.application"\n')
    f.write('CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}\n')
