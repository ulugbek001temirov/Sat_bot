import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sat_bot_project.settings')
django.setup()

from bot.handler import run

if __name__ == '__main__':
    run()