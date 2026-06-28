with open('c:/Users/saura/ParseOps/backend/config/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_apps = """INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "users",
    "organizations",
    "dashboard",
    "notifications",
    "notes",
    "goals",
    "tasks",
    "analytics",
]"""

new_apps = """INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "users",
    "organizations",
    "dashboard",
    "notifications",
    "notes",
    "goals",
    "tasks",
    "analytics",
    "chat",
    "channels",
]"""

if old_apps in content:
    content = content.replace(old_apps, new_apps)
    with open('c:/Users/saura/ParseOps/backend/config/settings.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched INSTALLED_APPS")
else:
    print("Not found")
