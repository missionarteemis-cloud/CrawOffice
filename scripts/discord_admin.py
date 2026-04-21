#!/usr/bin/env python3
"""
discord_admin.py — Gestione amministrativa Discord via API diretta.
Usato da OpenClaw come workaround per azioni non supportate dal tool nativo.

Uso:
  python3 discord_admin.py create-channel --name "nuovo-canale" --type text
  python3 discord_admin.py create-channel --name "vocale-team" --type voice
  python3 discord_admin.py create-channel --name "annunci" --type text --category "CATEGORIA_ID"
  python3 discord_admin.py delete-channel --id "CHANNEL_ID"
  python3 discord_admin.py create-category --name "TEAM ALPHA"
  python3 discord_admin.py list-channels
  python3 discord_admin.py set-permissions --channel-id "ID" --role-id "ID" --allow "VIEW_CHANNEL,SEND_MESSAGES"
  python3 discord_admin.py read-messages --channel-id "ID" --limit 20
  python3 discord_admin.py delete-message --channel-id "ID" --message-id "ID"
  python3 discord_admin.py create-thread --channel-id "ID" --name "Nome thread" --message "Primo messaggio"
  python3 discord_admin.py thread-from-message --channel-id "ID" --message-id "ID" --name "Nome thread"
  python3 discord_admin.py list-threads --channel-id "ID"
"""

import sys
import os
import json
import argparse
import time
import urllib.request
import urllib.error
from pathlib import Path

# Config
ENV_PATH   = Path.home() / ".openclaw" / ".env"
GUILD_ID   = "1495429636111204403"
API_BASE   = "https://discord.com/api/v10"

CHANNEL_TYPES = {
    "text": 0,
    "voice": 2,
    "category": 4,
    "announcement": 5,
    "thread": 11,
    "forum": 15
}

PERMISSION_FLAGS = {
    "VIEW_CHANNEL":        1 << 10,
    "SEND_MESSAGES":       1 << 11,
    "READ_MESSAGE_HISTORY":1 << 16,
    "ATTACH_FILES":        1 << 15,
    "EMBED_LINKS":         1 << 14,
    "USE_SLASH_COMMANDS":  1 << 31,
    "MANAGE_MESSAGES":     1 << 13,
    "MANAGE_CHANNELS":     1 << 4,
    "CONNECT":             1 << 20,
    "SPEAK":               1 << 21,
}


def load_env(path):
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_bot_token():
    env = load_env(ENV_PATH)
    token = env.get("DISCORD_BOT_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ DISCORD_BOT_TOKEN non trovato in ~/.openclaw/.env")
        sys.exit(1)
    return token


def api_request(method, endpoint, payload=None, max_retries=5):
    token = get_bot_token()
    url   = f"{API_BASE}{endpoint}"
    data  = json.dumps(payload).encode() if payload else None

    attempt = 0
    while True:
        req = urllib.request.Request(
            url, data=data,
            headers={
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json",
                "User-Agent": "OpenClaw-AdminScript/1.0"
            },
            method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            if e.code == 429 and attempt < max_retries:
                retry_after = 1.0
                try:
                    parsed = json.loads(error_body)
                    retry_after = float(parsed.get("retry_after", 1.0))
                except Exception:
                    pass
                retry_after = max(retry_after, 0.5)
                print(f"⏳ Rate limit Discord (429), attendo {retry_after:.2f}s e riprovo...")
                time.sleep(retry_after)
                attempt += 1
                continue
            print(f"❌ Discord API error {e.code}: {error_body}")
            sys.exit(1)


def create_channel(name, channel_type="text", category_id=None, topic=None, position=None):
    """Crea un canale nel server."""
    payload = {
        "name": name,
        "type": CHANNEL_TYPES.get(channel_type, 0)
    }
    if category_id:
        payload["parent_id"] = category_id
    if topic:
        payload["topic"] = topic
    if position is not None:
        payload["position"] = position

    result = api_request("POST", f"/guilds/{GUILD_ID}/channels", payload)
    print(f"✅ Canale creato: #{result['name']} (ID: {result['id']}, tipo: {channel_type})")
    return result


def delete_channel(channel_id):
    """Elimina un canale."""
    api_request("DELETE", f"/channels/{channel_id}")
    print(f"✅ Canale eliminato (ID: {channel_id})")


def create_category(name, position=None):
    """Crea una categoria."""
    payload = {
        "name": name,
        "type": CHANNEL_TYPES["category"]
    }
    if position is not None:
        payload["position"] = position

    result = api_request("POST", f"/guilds/{GUILD_ID}/channels", payload)
    print(f"✅ Categoria creata: {result['name']} (ID: {result['id']})")
    return result


def list_channels():
    """Lista tutti i canali del server."""
    channels = api_request("GET", f"/guilds/{GUILD_ID}/channels")
    categories = {c["id"]: c["name"] for c in channels if c["type"] == 4}

    print(f"\n📋 Canali del server ({len(channels)} totali):\n")

    for cat_id, cat_name in sorted(categories.items(), key=lambda x: x[1]):
        print(f"📁 {cat_name} (ID: {cat_id})")
        for ch in sorted([c for c in channels if c.get("parent_id") == cat_id],
                         key=lambda x: x.get("position", 0)):
            type_icon = "🔊" if ch["type"] == 2 else "#"
            print(f"   {type_icon} {ch['name']} (ID: {ch['id']})")

    orphans = [c for c in channels if not c.get("parent_id") and c["type"] != 4]
    if orphans:
        print(f"\n📁 (nessuna categoria)")
        for ch in orphans:
            type_icon = "🔊" if ch["type"] == 2 else "#"
            print(f"   {type_icon} {ch['name']} (ID: {ch['id']})")

    return channels


def set_permissions(channel_id, role_id, allow_perms=None, deny_perms=None):
    """Imposta i permessi di un ruolo su un canale."""
    allow_bits = 0
    deny_bits  = 0

    if allow_perms:
        for perm in allow_perms.split(","):
            perm = perm.strip().upper()
            if perm in PERMISSION_FLAGS:
                allow_bits |= PERMISSION_FLAGS[perm]
            else:
                print(f"⚠️  Permesso sconosciuto: {perm}")

    if deny_perms:
        for perm in deny_perms.split(","):
            perm = perm.strip().upper()
            if perm in PERMISSION_FLAGS:
                deny_bits |= PERMISSION_FLAGS[perm]
            else:
                print(f"⚠️  Permesso sconosciuto: {perm}")

    payload = {
        "allow": str(allow_bits),
        "deny":  str(deny_bits),
        "type":  0
    }

    api_request("PUT", f"/channels/{channel_id}/permissions/{role_id}", payload)
    print(f"✅ Permessi aggiornati sul canale {channel_id} per il ruolo {role_id}")
    print(f"   Allow: {allow_bits} | Deny: {deny_bits}")


def edit_channel(channel_id, name=None, topic=None, position=None):
    """Modifica un canale esistente."""
    payload = {}
    if name:     payload["name"]     = name
    if topic:    payload["topic"]    = topic
    if position: payload["position"] = position

    result = api_request("PATCH", f"/channels/{channel_id}", payload)
    print(f"✅ Canale modificato: #{result['name']} (ID: {result['id']})")
    return result


def read_messages(channel_id, limit=20):
    """Legge i messaggi recenti di un canale con info utili su autore e reazioni."""
    messages = api_request("GET", f"/channels/{channel_id}/messages?limit={limit}")
    if not messages:
        print(f"📭 Nessun messaggio trovato nel canale {channel_id}")
        return []

    print(f"\n📨 Ultimi {len(messages)} messaggi nel canale {channel_id}:\n")
    for msg in reversed(messages):
        author = msg.get("author", {}).get("username", "?")
        content = (msg.get("content") or "").replace("\n", " ").strip()
        content = content[:120] + ("..." if len(content) > 120 else "")
        reactions = msg.get("reactions", []) or []
        reaction_text = ""
        if reactions:
            parts = []
            for r in reactions:
                emoji = r.get("emoji", {}).get("name", "?")
                count = r.get("count", 0)
                parts.append(f"{emoji}x{count}")
            reaction_text = " | reazioni: " + ", ".join(parts)
        print(f"- ID: {msg.get('id')} | autore: {author} | testo: {content or '[vuoto]'}{reaction_text}")
    return messages


def delete_message(channel_id, message_id):
    """Elimina un messaggio specifico da un canale."""
    api_request("DELETE", f"/channels/{channel_id}/messages/{message_id}")
    print(f"✅ Messaggio eliminato: {message_id} dal canale {channel_id}")


def delete_messages(channel_id, message_ids):
    """Elimina più messaggi, gestendo automaticamente eventuali rate limit."""
    total = len(message_ids)
    for idx, message_id in enumerate(message_ids, start=1):
        delete_message(channel_id, message_id)
        if idx < total:
            time.sleep(0.35)
    print(f"✅ Eliminazione multipla completata: {total} messaggi rimossi dal canale {channel_id}")


def create_thread(channel_id, name, message=None, auto_archive=1440):
    """
    Crea un thread standalone in un canale testuale.
    Non richiede un messaggio esistente — crea il thread da zero.
    auto_archive: minuti prima dell'archiviazione automatica (60, 1440, 4320, 10080)
    """
    payload = {
        "name": name,
        "auto_archive_duration": auto_archive,
        "type": 11  # GUILD_PUBLIC_THREAD
    }
    if message:
        payload["message"] = {"content": message}

    result = api_request("POST", f"/channels/{channel_id}/threads", payload)
    thread_id = result.get("id") or result.get("thread", {}).get("id", "?")
    thread_name = result.get("name") or result.get("thread", {}).get("name", name)
    print(f"✅ Thread creato: '{thread_name}' (ID: {thread_id})")
    print(f"   Canale padre: {channel_id}")
    if message:
        print(f"   Primo messaggio: '{message[:60]}{'...' if len(message) > 60 else ''}'")
    return result


def thread_from_message(channel_id, message_id, name, auto_archive=1440):
    """
    Crea un thread a partire da un messaggio esistente.
    Il messaggio diventa il punto di partenza del thread.
    auto_archive: minuti prima dell'archiviazione automatica (60, 1440, 4320, 10080)
    """
    payload = {
        "name": name,
        "auto_archive_duration": auto_archive
    }

    result = api_request("POST", f"/channels/{channel_id}/messages/{message_id}/threads", payload)
    thread_id   = result.get("id", "?")
    thread_name = result.get("name", name)
    print(f"✅ Thread creato dal messaggio {message_id}: '{thread_name}' (ID: {thread_id})")
    return result


def send_message_to_thread(thread_id, content):
    """Invia un messaggio in un thread esistente."""
    payload = {"content": content}
    result = api_request("POST", f"/channels/{thread_id}/messages", payload)
    print(f"✅ Messaggio inviato nel thread {thread_id}: '{content[:60]}{'...' if len(content) > 60 else ''}'")
    return result


def list_threads(channel_id):
    """Lista i thread attivi in un canale."""
    result = api_request("GET", f"/guilds/{GUILD_ID}/threads/active")
    threads = [t for t in result.get("threads", []) if t.get("parent_id") == channel_id]

    if not threads:
        print(f"📋 Nessun thread attivo nel canale {channel_id}")
        return []

    print(f"\n🧵 Thread attivi nel canale {channel_id} ({len(threads)} totali):\n")
    for t in threads:
        archived = "📦" if t.get("thread_metadata", {}).get("archived") else "🟢"
        print(f"   {archived} {t['name']} (ID: {t['id']})")

    return threads


def main():
    parser = argparse.ArgumentParser(
        description="Discord Admin Tool — gestione canali, thread e permessi via API"
    )
    subparsers = parser.add_subparsers(dest="command")

    # create-channel
    p_create = subparsers.add_parser("create-channel", help="Crea un canale")
    p_create.add_argument("--name",     required=True)
    p_create.add_argument("--type",     default="text",
                          choices=["text", "voice", "announcement", "forum"])
    p_create.add_argument("--category", help="ID categoria parent")
    p_create.add_argument("--topic")
    p_create.add_argument("--position", type=int)

    # delete-channel
    p_delete = subparsers.add_parser("delete-channel", help="Elimina un canale")
    p_delete.add_argument("--id", required=True)

    # create-category
    p_cat = subparsers.add_parser("create-category", help="Crea una categoria")
    p_cat.add_argument("--name",     required=True)
    p_cat.add_argument("--position", type=int)

    # list-channels
    subparsers.add_parser("list-channels", help="Lista tutti i canali")

    # set-permissions
    p_perms = subparsers.add_parser("set-permissions", help="Imposta permessi canale")
    p_perms.add_argument("--channel-id", required=True)
    p_perms.add_argument("--role-id",    required=True)
    p_perms.add_argument("--allow")
    p_perms.add_argument("--deny")

    # read-messages
    p_read = subparsers.add_parser("read-messages", help="Legge i messaggi recenti di un canale")
    p_read.add_argument("--channel-id", required=True)
    p_read.add_argument("--limit", type=int, default=20)

    # delete-message
    p_dm = subparsers.add_parser("delete-message", help="Elimina un messaggio specifico")
    p_dm.add_argument("--channel-id", required=True)
    p_dm.add_argument("--message-id", required=True)

    # delete-messages
    p_dms = subparsers.add_parser("delete-messages", help="Elimina più messaggi")
    p_dms.add_argument("--channel-id", required=True)
    p_dms.add_argument("--message-ids", nargs="+", required=True)

    # edit-channel
    p_edit = subparsers.add_parser("edit-channel", help="Modifica un canale")
    p_edit.add_argument("--id",       required=True)
    p_edit.add_argument("--name")
    p_edit.add_argument("--topic")
    p_edit.add_argument("--position", type=int)

    # create-thread
    p_thread = subparsers.add_parser("create-thread",
                                      help="Crea un thread standalone in un canale")
    p_thread.add_argument("--channel-id",   required=True, help="ID del canale padre")
    p_thread.add_argument("--name",         required=True, help="Nome del thread")
    p_thread.add_argument("--message",      help="Primo messaggio nel thread (opzionale)")
    p_thread.add_argument("--auto-archive", type=int, default=1440,
                          choices=[60, 1440, 4320, 10080],
                          help="Minuti prima dell'archiviazione (default: 1440 = 1 giorno)")

    # thread-from-message
    p_tfm = subparsers.add_parser("thread-from-message",
                                   help="Crea un thread da un messaggio esistente")
    p_tfm.add_argument("--channel-id",  required=True, help="ID del canale")
    p_tfm.add_argument("--message-id",  required=True, help="ID del messaggio da cui creare il thread")
    p_tfm.add_argument("--name",        required=True, help="Nome del thread")
    p_tfm.add_argument("--auto-archive", type=int, default=1440,
                       choices=[60, 1440, 4320, 10080])

    # send-to-thread
    p_send = subparsers.add_parser("send-to-thread", help="Invia un messaggio in un thread")
    p_send.add_argument("--thread-id", required=True, help="ID del thread")
    p_send.add_argument("--message",   required=True, help="Testo del messaggio")

    # list-threads
    p_lt = subparsers.add_parser("list-threads", help="Lista thread attivi in un canale")
    p_lt.add_argument("--channel-id", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "create-channel":
        create_channel(args.name, args.type, args.category, args.topic, args.position)

    elif args.command == "delete-channel":
        confirm = input(f"⚠️  Sicuro di voler eliminare il canale {args.id}? (s/N): ")
        if confirm.lower() == "s":
            delete_channel(args.id)
        else:
            print("Annullato.")

    elif args.command == "create-category":
        create_category(args.name, args.position)

    elif args.command == "list-channels":
        list_channels()

    elif args.command == "set-permissions":
        set_permissions(args.channel_id, args.role_id, args.allow, args.deny)

    elif args.command == "read-messages":
        read_messages(args.channel_id, args.limit)

    elif args.command == "delete-message":
        delete_message(args.channel_id, args.message_id)

    elif args.command == "delete-messages":
        delete_messages(args.channel_id, args.message_ids)

    elif args.command == "edit-channel":
        edit_channel(args.id, args.name, args.topic, args.position)

    elif args.command == "create-thread":
        create_thread(args.channel_id, args.name, args.message, args.auto_archive)

    elif args.command == "thread-from-message":
        thread_from_message(args.channel_id, args.message_id, args.name, args.auto_archive)

    elif args.command == "send-to-thread":
        send_message_to_thread(args.thread_id, args.message)

    elif args.command == "list-threads":
        list_threads(args.channel_id)


if __name__ == "__main__":
    main()
