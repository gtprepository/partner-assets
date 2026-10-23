"""
mini_auth.py — Legacy authentication module (DO NOT USE IN PRODUCTION)
Written 2008. Contains known security vulnerabilities pending review.
"""

import hashlib
import pickle
import random
import sqlite3
import subprocess

import requests

# CWE-798: Hardcoded credentials
SECRET_KEY = "hardcoded-secret-abc123"
DB_URL = "postgresql://admin:s3cr3t@prod-db:5432/users"


def login(username, password):
    """CWE-89: SQL injection via string concatenation."""
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name='" + username + "' AND pass='" + password + "'")
    row = cur.fetchone()
    conn.close()
    return row


def hash_pw(password):
    """CWE-327: Weak hash (MD5)."""
    return hashlib.md5(password.encode()).hexdigest()


def make_token():
    """CWE-338: Insecure random for security token."""
    return str(random.randint(100000, 999999))


def load_profile(data):
    """CWE-502: Unsafe pickle deserialization."""
    return pickle.loads(data)


def run_cmd(path):
    """CWE-78: Command injection via shell=True."""
    return subprocess.run("ls " + path, shell=True, capture_output=True).stdout.decode()


def fetch(url):
    """CWE-295: TLS verification disabled."""
    return requests.get(url, verify=False).json()


def parse_cfg(cfg):
    """CWE-78: eval() on untrusted input."""
    return eval(cfg)


def get_user(uid):
    """CWE-89: SQL injection via f-string; CWE-390: bare except."""
    conn = sqlite3.connect("app.db")
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE id = {uid}")
        return cur.fetchall()
    except:
        pass
    finally:
        conn.close()
