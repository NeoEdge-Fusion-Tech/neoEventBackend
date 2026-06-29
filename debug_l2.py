import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

query = """
    SELECT 
        b.email, 
        pf.photo_id, 
        b.face_encoding <-> pf.face_embedding AS l2_distance,
        b.face_encoding <=> pf.face_embedding AS cosine_distance
    FROM accounts_biometricidentity b
    CROSS JOIN photos_photoface pf
"""

with connection.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

print("Distance Measurements:")
for row in results:
    print(f"Email: {row[0]}, Photo: {row[1]}")
    print(f"  L2 Distance: {row[2]}")
    print(f"  Cosine Distance: {row[3]}")
