#!/usr/bin/env python
"""
ZAP Authentication Hook Script
"""

import urllib.request
import urllib.parse
import re

def zap_started(zap, target):
    print("[*] Authenticating to target...")
    
    login_url = "http://tiwap:5000/login"
    credentials = urllib.parse.urlencode({
        'username': 'admin',
        'password': 'admin'
    }).encode()
    
    try:
        req = urllib.request.Request(login_url, data=credentials)
        response = urllib.request.urlopen(req)
        
        cookie_header = response.headers.get('Set-Cookie', '')
        
        if 'session=' in cookie_header:
            session_match = re.search(r'session=([^;]+)', cookie_header)
            if session_match:
                session_value = session_match.group(1)
                print(f"[+] Got session: {session_value[:30]}...")
                
                zap.replacer.add_rule(
                    description="Auth Session",
                    enabled=True,
                    matchtype="REQ_HEADER",
                    matchregex=False,
                    matchstring="Cookie",
                    replacement=f"session={session_value}"
                )
                print("[+] Session cookie added to ZAP")
        else:
            print("[-] No session cookie found")
            
    except Exception as e:
        print(f"[-] Authentication failed: {e}")