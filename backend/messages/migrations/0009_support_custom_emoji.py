# Generated manually for custom emoji reaction validation.

import messages.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat_messages", "0008_add_read_state_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reaction",
            name="emoji",
            field=models.CharField(
                max_length=255,
                validators=[messages.models.validate_reaction_emoji],
            ),
        ),
    ]
