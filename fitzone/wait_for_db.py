import time
import psycopg2
import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        max_retries = 30
        for i in range(max_retries):
            try:
                conn = psycopg2.connect(
                    dbname=os.getenv('DB_NAME', 'fitZone_DB'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', '1'),
                    host=os.getenv('DB_HOST', 'db'),
                    port=os.getenv('DB_PORT', '5432')
                )
                conn.close()
                self.stdout.write(self.style.SUCCESS('Database available!'))
                return
            except psycopg2.OperationalError:
                self.stdout.write(f'Database unavailable, waiting 1 second... ({i+1}/{max_retries})')
                time.sleep(1)
        
        self.stdout.write(self.style.ERROR('Database not available after 30 seconds!'))
        exit(1)