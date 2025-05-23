# Generated by Django 5.1.7 on 2025-03-24 16:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_userlocation_user_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_type', models.CharField(choices=[('police', 'Police Station'), ('complainant', 'Complainant')], max_length=20)),
                ('content', models.TextField()),
                ('attachment', models.FileField(blank=True, null=True, upload_to='message_attachments/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('complaint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='core.complaint')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
