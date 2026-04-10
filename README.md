# Exim4-Discord-Transport
This project provides a very simple solution to forward incoming emails from an **Exim4** mail server to a **Discord** channel via Webhooks. It intelligently handles multipart MIME messages, strips HTML when necessary, and ensures messages fit within Discord's constraints.

---

## Features

* **Smart Parsing:** Extracts the `text/plain` part of an email. If only HTML is available, it strips the tags and converts it to readable text.
* **Attachment Filter:** Automatically ignores attachments and images.
* **Graceful Truncation:** Crops messages to 1900 characters to avoid Discord's 2000-character limit.
* **Error Awareness:** Communicates connection failures back to Exim, allowing the mail server to retry delivery later if Discord is down.
* **Dual Delivery Support:** Can be configured to forward mail to Discord while still delivering a copy to the user's local inbox.

---

## 1. The Script (`exim_to_discord.py`)

Save this file to `/usr/local/bin/exim_to_discord.py`.

---

## 2. Installation & Permissions

Ensure the script is executable and owned by the user running the Exim process (typically `exim` or `Debian-exim`).

```bash
chmod +x /usr/local/bin/exim_to_discord.py
chown exim:exim /usr/local/bin/exim_to_discord.py
```

---

## 3. Exim Configuration

To implement this transport for a specific user (e.g., `xyz`) while maintaining normal inbox delivery, add the following to your Exim configuration:

### The Transport
Add this block to the **transports** section of your configuration (e.g., /etc/exim4/exim4.conf.template, or `/etc/exim4/conf.d/transport/`):

```exim
discord_pipe:
  driver = pipe
  command = /usr/local/bin/exim_to_discord.py
  user = Debian-exim
  group = Debian-exim
  return_fail_output = true
  log_output = true
  temp_errors = *
```

### The Router
Add this block to the **routers** section. **Important:** Place this at the very top of your routers so it triggers before local delivery.

```exim
discord_forward_xyz:
  driver = accept
  condition = ${if eq{$local_part}{xyz}}
  transport = discord_pipe
  unseen
```

### Why use `unseen`?
The `unseen` directive is the magic here. It tells Exim to process this router (sending the mail to Discord) and then immediately pass the message to the *next* router as if nothing happened. This ensures the user `xyz` receives the email in their standard inbox **and** on Discord.

---

## 3. Apply Changes
    
* Test the configuration: ```exim -bV``` (to check for syntax errors).
* Restart Exim: ```systemctl restart exim4```.

---

## 4. Troubleshooting
* **Logs:** Check your Exim main log (usually `/var/log/exim4/mainlog`) for any "piped to discord_pipe" entries.
* **Failures:** If the script exits with an error (e.g., timeout), Exim will keep the email in the queue and retry delivery to Discord based on your retry rules, but the "unseen" copy will still be delivered to the local inbox immediately.
