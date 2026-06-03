# Generated manually for adding MessageReadState index

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_messages', '0007_purge_soft_deleted_messages'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='messagereadstate',
            index=models.Index(fields=['user', 'room'], name='read_state_user_room_idx'),
        ),
    ]
