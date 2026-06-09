from django.db import migrations, models

import users.avatar_service


STORED_DEFAULT_AVATAR_PATHS = (
    "avatars/Password_defualt.jpg",
    "avatars/OAuth_defualt.jpg",
    "avatars/Password_defualt.svg",
    "avatars/OAuth_defualt.svg",
)


def clear_stored_default_avatars(apps, schema_editor):
    profile_model = apps.get_model("users", "Profile")
    profile_model.objects.filter(image__in=STORED_DEFAULT_AVATAR_PATHS).update(image="")


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_profile_image_default_from_env"),
    ]

    operations = [
        migrations.RunPython(clear_stored_default_avatars, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="profile",
            name="image",
            field=models.ImageField(
                blank=True,
                upload_to=users.avatar_service.profile_avatar_upload_to,
            ),
        ),
    ]
