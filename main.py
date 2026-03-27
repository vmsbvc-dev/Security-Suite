# -------------------------------------------------------------------------
# HASSAN AI VAULT - v111 (Elite Edition)
# -------------------------------------------------------------------------
# DISCLAIMER: Educational purposes & ethical hacking only.
# -------------------------------------------------------------------------

import os, math, asyncio, httpx, re, warnings, random, base64, ujson, zipfile, psutil, time, socket, ipaddress, csv, hashlib

# Mute Deprecation Warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import lightgbm as lgb
import cloudscraper  
import aiofiles 
import certifi 
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from urllib.parse import urljoin 

# --- Deep Extraction Libraries ---
try:
    import rarfile, PyPDF2, openpyxl, exifread, pytesseract
    from docx import Document
    from striprtf.striprtf import rtf_to_text
    from pdfminer.high_level import extract_text as pdf_extract
    import joblib
    from tqdm import tqdm
    import whois  
    import dns.resolver 
    import aiodns
    from pyaxmlparser import APK
    from bs4 import BeautifulSoup
    from wafw00f.main import WAFW00F 
    
    import sublist3r 
    from DrissionPage import ChromiumPage 
    import jwt 
    import sqlparse
    import paramiko
    import phonenumbers
    from email_validator import validate_email
    
    # --- PwnTools Integration ---
    try:
        from pwn import ELF, context, remote
        PWN_AVAILABLE = True
    except ImportError:
        PWN_AVAILABLE = False

    try: from retrying import retry 
    except ImportError:
        def retry(*args, **kwargs): return lambda f: f

    from colorama import Fore, Style, init 
    init(autoreset=True) 
    G, R, C, Y, P, B, RS = Fore.GREEN, Fore.RED, Fore.CYAN, Fore.YELLOW, Fore.MAGENTA, Fore.BLUE, Style.RESET_ALL
except Exception as e:
    G = R = C = Y = P = B = RS = ""
    if 'retry' not in globals():
        def retry(*args, **kwargs): return lambda f: f

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError: pass

# --- Path Configuration ---
BASE_PATH = os.getcwd()
DOWNLOAD_DIR = os.path.join(BASE_PATH, "downloads")
KEY_MEGA_CSV = os.path.join(BASE_PATH, "key_results.csv")
IP_MEGA_CSV = os.path.join(BASE_PATH, "ip_results.csv")
APK_HASH_CSV = os.path.join(BASE_PATH, "apk_hashes.csv")

EXT_LIST = ['.js', '.json', '.env', '.xml', '.txt', '.conf', '.log', '.zip', '.sql', '.bak', '.config', '.yaml', '.yml', '.py', '.sh', '.key', '.pem', '.aspx', '.asp', '.jsp', '.php', '.db', '.sqlite']

for d in [DOWNLOAD_DIR]:
    if not os.path.exists(d): os.makedirs(d, exist_ok=True)

class HassanAI_Vault:
    def __init__(self, target_url, admin_mode=False): 
        self.raw_target = target_url.replace("https://", "").replace("http://", "").split('/')[0]
        self.target = "https://" + self.raw_target
        self.domain = self.raw_target
        self.admin_mode = admin_mode
        self.visited_urls = set()
        self.downloaded_files = set()
        self.queue = asyncio.Queue()
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android'})
        
        self.patterns = {
            "Google_Key": r'AIza[0-9A-Za-z-_]{35}',
            "Firebase": r'https://[a-z0-9.-]+\.firebaseio\.com',
            "AWS_Key": r'AKIA[0-9A-Z]{16}',
            "FB_Token": r'EAACEdEose0cBA[A-Za-z0-9]+',
            "JWT_Token": r'ey[a-zA-Z0-9]{50,}\.ey[a-zA-Z0-9]{50,}\.[a-zA-Z0-9_-]+',
            "Email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "Phone": r'\+?[1-9]\d{1,14}',
            "IP_Addr": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "SQL_Query": r'(SELECT\s+.*\s+FROM\s+.*|INSERT\s+INTO\s+.*|UPDATE\s+.*SET\s+.*)',
            "Sensitive_Path": r'/(?:config|admin|backup|v1|api|debug|env)/[a-zA-Z0-9\._/-]+'
        }
        self._prepare_csvs()

    def _prepare_csvs(self):
        files_headers = [(KEY_MEGA_CSV, ['Timestamp', 'Type', 'Data', 'Source']), (IP_MEGA_CSV, ['Timestamp', 'IP', 'Type', 'Source']), (APK_HASH_CSV, ['Package_Name', 'Last_Hash', 'Last_Seen'])]
        for file, headers in files_headers:
            if not os.path.exists(file):
                with open(file, 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerow(headers)

    # --- [New Suggestion for Pwn Path [b]] ---
    async def deep_binary_strings(self, file_path):
        """اكتشاف النصوص الحساسة داخل ملفات الـ Binary"""
        print(f"   🔍 {P}[STRINGS-MINING]{RS} Hunting sensitive text...")
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                found_strings = re.findall(rb"[\x20-\x7E]{6,}", content)
                for s in found_strings[:20]:
                    decoded_s = s.decode(errors='ignore')
                    if any(x in decoded_s.lower() for x in ['pass', 'key', 'admin', 'http', 'mysql']):
                        print(f"      🔥 {G}[SENSITIVE-STRING]{RS} {decoded_s}")
                        await self.save_key_to_mega("Pwn_String", decoded_s, file_path)
        except: pass

    async def pwn_binary_analysis(self, file_path):
        if not PWN_AVAILABLE: 
            print(f" {R}[!] Pwntools not installed.{RS}")
            return
        try:
            print(f"\n   🛡️ {B}[PWN-ANALYSIS]{RS} Analyzing: {os.path.basename(file_path)}")
            await self.deep_binary_strings(file_path)
            
            context.clear()
            context.os = 'android'
            context.arch = 'arm64'
            
            elf = ELF(file_path, checksec=False)
            has_rwx = any(seg.header.p_flags & 7 == 7 for seg in elf.segments)
            
            # مصفوفة النتائج مع التفسير لربطها بوضع [x]
            analysis_data = [
                ("RELRO", elf.relro, {
                    2: (f"{G}Full RELRO", "✅ Safe from GOT overwrite."),
                    1: (f"{Y}Partial RELRO", "⚠️ Potential GOT risk."),
                    0: (f"{R}No RELRO", "🔥 GOT Hijacking Possible!")
                }),
                ("Stack Canary", 1 if elf.canary else 0, {
                    1: (f"{G}Enabled", "✅ Detects Overflows."),
                    0: (f"{R}No Canary", "🔥 Vulnerable to Buffer Overflow.")
                }),
                ("NX (No-Execute)", 1 if elf.nx else 0, {
                    1: (f"{G}Enabled", "✅ Stack is non-executable."),
                    0: (f"{R}Disabled", "🔥 Code can run from Stack!")
                }),
                ("PIE (ASLR)", 1 if elf.pie else 0, {
                    1: (f"{G}Enabled", "✅ Random memory addresses."),
                    0: (f"{R}No PIE", "🔥 Fixed addresses (Easy ROP).")
                })
            ]

            print(f"   {'-'*65}")
            critical_vuln = False 
            for label, value, mapping in analysis_data:
                status, hint = mapping.get(value, (f"{R}Unknown", ""))
                print(f"   {C}{label.ljust(18)}: {status.ljust(25)} {RS}| {P}{hint}{RS}")
                if "🔥" in hint: critical_vuln = True 

            rwx_status = f"{R}Found (Critical!)" if has_rwx else f"{G}Not Found"
            if has_rwx: critical_vuln = True
            print(f"   {C}{'RWX Segments'.ljust(18)}: {rwx_status.ljust(25)} {RS}| {P}{'Dangerous memory!' if has_rwx else 'Safe.'}{RS}")
            print(f"   {'-'*65}\n")

            # الاقتراح الذكي: الانتقال لـ [x] في حال وجود ثغرات
            if critical_vuln:
                print(f"   ⚠️ {R}[CRITICAL VULNERABILITY DETECTED]{RS}")
                choice = input(f"   {Y}Do you want to switch to [x] mode for deep exploit scanning? (y/n): {RS}").lower()
                if choice == 'y':
                    print(f"   🚀 {G}Launching Deep Exploit Scan [x]...{RS}")
                    await self.start() 

            for label, value, _ in analysis_data:
                await self.save_key_to_mega("PWN_Check", f"{label}:{value}", file_path)
        except Exception as e: 
            print(f" {R}[!] Pwn Analysis Error: {e}{RS}")

    async def download_file(self, file_url):
        if file_url in self.downloaded_files: return
        self.downloaded_files.add(file_url)
        try:
            loop = asyncio.get_event_loop()
            r = await loop.run_in_executor(None, lambda: self.scraper.get(file_url, timeout=10))
            if r.status_code == 200:
                fname = f"{int(time.time())}_{file_url.split('/')[-1].split('?')[0]}"
                async with aiofiles.open(os.path.join(DOWNLOAD_DIR, fname), 'wb') as f: await f.write(r.content)
                print(f"   📥 {G}[DOWNLOADED]{RS} {fname}")
                await self.deep_file_miner(os.path.join(DOWNLOAD_DIR, fname), file_url)
        except: pass

    async def analyze_apk(self, target_input):
        if target_input in self.downloaded_files: return
        self.downloaded_files.add(target_input)
        filename = ""
        is_local = os.path.exists(target_input)
        try:
            if is_local: filename = target_input
            else:
                filename = os.path.join(DOWNLOAD_DIR, target_input.split('/')[-1])
                if not filename.endswith('.apk'): filename += ".apk"
                print(f"   📥 {Y}[APK-DOWNLOAD]{RS} Fetching...")
                async with httpx.AsyncClient(verify=False, timeout=60) as client:
                    resp = await client.get(target_input)
                    if resp.status_code == 200:
                        async with aiofiles.open(filename, "wb") as f: await f.write(resp.content)
            apk_obj = APK(filename)
            print(f"   📱 {G}[APK-FOUND]{RS} {apk_obj.package}")
            await self.deep_file_miner(filename, target_input)
            if not is_local: os.remove(filename)
        except Exception as e: print(f" {R}[APK-ERROR]{RS} {e}")

    async def save_key_to_mega(self, name, data, url):
        try:
            async with aiofiles.open(KEY_MEGA_CSV, mode='a', newline='', encoding='utf-8') as f:
                row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, str(data).replace(",", "|"), url]
                await f.write(",".join(row) + "\n")
        except: pass

    async def deep_file_miner(self, file_path, url):
        ext = os.path.splitext(file_path)[1].lower()
        text_content = ""
        try:
            if ext in ['.zip', '.rar', '.apk']:
                with zipfile.ZipFile(file_path, 'r') as z:
                    text_content = " ".join(z.namelist())
                    for name in z.namelist()[:30]: 
                        if name.endswith(('.xml', '.json', '.txt', '.env')):
                            with z.open(name) as f: text_content += f.read().decode(errors='ignore')
            elif ext in ['.js', '.html', '.txt', '.env', '.json']:
                async with aiofiles.open(file_path, 'r', errors='ignore') as f: text_content = await f.read()
            if text_content:
                for name, pattern in self.patterns.items():
                    matches = re.findall(pattern, text_content)
                    for m in set(matches): await self.save_key_to_mega(f"InFile_{name}", m, url)
        except: pass

    async def subdomain_enumeration(self):
        print(f" {Y}[ENUM]{RS} Hunting subdomains for: {self.domain}")
        try:
            subs = sublist3r.main(self.domain, 40, None, silent=True, verbose=False, engines=None)
            if subs:
                for s in subs: self.queue.put_nowait(f"https://{s}")
        except: pass

    async def get_banner(self, ip, port):
        """سحب معلومات الخدمة (Banner Grabbing)"""
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=2)
            if port == 80:
                writer.write(b"HEAD / HTTP/1.1\r\nHost: " + self.domain.encode() + b"\r\n\r\n")
                await writer.drain()
            banner = await asyncio.wait_for(reader.read(100), timeout=2)
            writer.close()
            await writer.wait_closed()
            return banner.decode(errors='ignore').strip()
        except: return None

    async def network_scan(self):
        print(f" {B}[NET-SCAN]{RS} Probing: {self.domain}")
        try:
            target_ip = socket.gethostbyname(self.domain)
            print(f"   📍 {C}[IP]{RS} {target_ip}")
            try:
                w = whois.whois(self.domain)
                print(f"   🏢 {G}[ORG]{RS} {w.org or 'Unknown'}")
            except: pass

            ports = {21: "FTP", 22: "SSH", 80: "HTTP", 443: "HTTPS", 3306: "MySQL"}
            for port, service in ports.items():
                try:
                    reader, writer = await asyncio.wait_for(asyncio.open_connection(target_ip, port), timeout=1.5)
                    print(f"   🔥 {G}[PORT-OPEN]{RS} {port} ({service})")
                    banner = await self.get_banner(target_ip, port)
                    if banner: print(f"      📝 {Y}[BANNER]{RS} {banner[:50]}...")
                    writer.close()
                    await writer.wait_closed()
                except: continue
                
            if target_ip in ["127.0.0.1", "localhost"]:
                print(f"\n {Y}[LOCAL-MGMT]{RS} You are scanning yourself.")
                choice = input(f" {C}Do you want to block a port? (Enter port number or 'n'): {RS}").strip().lower()
                if choice.isdigit():
                    os.system(f"su -c 'iptables -A INPUT -p tcp --dport {choice} -j DROP'")
                    print(f" {R}[CLOSED]{RS} Port {choice} has been blocked.")
        except Exception as e: print(f" {R}[NET-ERROR]{RS} {e}")

    async def worker(self, sem):
        while True:
            url = await self.queue.get()
            if url in self.visited_urls or len(self.visited_urls) > 3000:
                self.queue.task_done(); continue
            self.visited_urls.add(url)
            async with sem:
                res = await self.fetch_page(url)
                if res and res[0]:
                    print(f" {C}[SCAN]{RS} {url[:60]}")
                    for name, p in self.patterns.items():
                        matches = re.findall(p, res[0])
                        for m in set(matches):
                            print(f"   🔥 {G}[{name}]{RS} Found!")
                            await self.save_key_to_mega(name, m, url)
                    links = re.findall(r'(?:href|src|url)=["\'](.*?)["\']', res[0])
                    for link in set(links):
                        full_url = urljoin(url, link)
                        if not full_url.startswith('http') or any(x in full_url for x in ['#', 'javascript']): continue
                        file_ext = os.path.splitext(full_url.split('?')[0])[1].lower()
                        if file_ext in EXT_LIST: asyncio.create_task(self.download_file(full_url))
                        elif self.domain in full_url: self.queue.put_nowait(full_url)
            self.queue.task_done()

    async def start(self):
        print(f"\n{P}⚡ HASSAN AI V111: ELITE EDITION ⚡{RS}")
        await self.subdomain_enumeration()
        for p in ["/", "/.env", "/robots.txt", "/config.php"]: self.queue.put_nowait(self.target + p)
        sem = asyncio.Semaphore(15) 
        workers = [asyncio.create_task(self.worker(sem)) for _ in range(8)]
        await self.queue.join()
        for w in workers: w.cancel()

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    async def fetch_page(self, url):
        headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36"}
        try:
            async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=12, headers=headers) as client:
                response = await client.get(url)
                return response.text, response.headers.get('Content-Type', '')
        except: return None, None

async def main_controller():
    print(f"\n{Y}[x] Domain | [k] APK | [m] Network | [b] Pwn Analysis{RS}")
    raw_input = input(f"{C}Select Mode: {RS}").strip().lower().split()
    mode = raw_input[-1] if raw_input else ""
    
    if mode == 'x':
        t_input = input(f"{G}Target (example.com): {RS}").strip().split()
        t = t_input[-1] if t_input else ""
        if t: await HassanAI_Vault(t).start()
    elif mode == 'k':
        t_input = input(f"{P}APK Path or Link: {RS}").strip().split()
        t = t_input[-1] if t_input else ""
        if t: await HassanAI_Vault(t).analyze_apk(t)
    elif mode == 'm':
        t_input = input(f"{B}Network Target: {RS}").strip().split()
        t = t_input[-1] if t_input else ""
        if t: await HassanAI_Vault(t).network_scan()
    elif mode == 'b':
        p_input = input(f"{P}Binary Path: {RS}").strip().split()
        path = p_input[-1] if p_input else ""
        if os.path.exists(path): await HassanAI_Vault("local").pwn_binary_analysis(path)

if __name__ == "__main__":
    try: asyncio.run(main_controller())
    except KeyboardInterrupt: print(f"\n{R}[!] Stopped.{RS}")
    
