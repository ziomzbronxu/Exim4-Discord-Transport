#!/usr/bin/env python3
import sys
import email
import email.policy
import json
import urllib.request
import re
import html

# --- CONFIGURATION ---
WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
MAX_LENGTH = 1900
TIMEOUT = 10  # Seconds to wait for Discord response
# ---------------------

def strip_html(html_content):
    """Basic HTML to Text conversion for emails without a plain text part."""
    html_content = re.sub(r'<style.*?>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<(br|p|div|tr|li|h[1-6])[^>]*>', '\n', html_content, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', html_content)
    text = html.unescape(text)
    return re.sub(r'\n\s*\n', '\n\n', text).strip()

def main():
    try:
        # Read raw email from stdin
        msg = email.message_from_file(sys.stdin, policy=email.policy.default)
        subject = msg.get('Subject', '(No Subject)')
        sender = msg.get('From', '(Unknown Sender)')
        
        body = ""
        html_body = ""
        
        for part in msg.walk():
            if part.is_multipart() or part.get_filename() is not None:
                continue
            
            content_type = part.get_content_type()
            try:
                content = part.get_content()
            except:
                continue

            if content_type == 'text/plain':
                body = content
                break
            elif content_type == 'text/html':
                html_body = content

        if not body and html_body:
            body = strip_html(html_body)
        if not body:
            body = "*[No readable text content]*"

        # Format and truncate
        discord_message = f"**From:** {sender}\n**Subject:** {subject}\n\n{body}"
        if len(discord_message) > MAX_LENGTH:
            discord_message = discord_message[:MAX_LENGTH] + "\n\n... *(truncated)*"

        payload = {"content": discord_message}
        req = urllib.request.Request(
            WEBHOOK_URL, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={'Content-Type': 'application/json', 'User-Agent': 'Exim-Discord-Bot'}
        )
        
        # Perform the request
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            if response.status not in [200, 204]:
                raise Exception(f"Discord API returned status {response.status}")

    except Exception as e:
        # Log error to stderr for Exim logs and exit with failure
        print(f"Discord Forwarding Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
