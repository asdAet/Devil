from django.db import migrations


STORED_DEFAULT_GROUP_AVATAR_PATHS = (
    "avatars/Group_defualt.jpg",
    "avatars/Group_defualt.svg",
)


def clear_stored_default_group_avatars(apps, schema_editor):
    room_model = apps.get_model("rooms", "Room")
    room_model.objects.filter(avatar__in=STORED_DEFAULT_GROUP_AVATAR_PATHS).update(avatar="")


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0006_remove_room_slug_alter_room_avatar_and_more"),
    ]

    operations = [
        migrations.RunPython(
            clear_stored_default_group_avatars,
            migrations.RunPython.noop,
        ),
    ]
