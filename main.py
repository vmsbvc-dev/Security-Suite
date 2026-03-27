# -------------------------------------------------------------------------
# HASSAN AI VAULT - v110 (Ultimate Edition)
# -------------------------------------------------------------------------
# DISCLAIMER:
# This tool is developed for educational purposes and ethical hacking only.
# Using this tool against targets without prior consent is illegal.
# The developer (Hassan) assumes no liability for any misuse or damage.
# -------------------------------------------------------------------------

import os, math, asyncio, httpx, re, warnings, random, base64, ujson, zipfile, psutil, time, socket, ipaddress, csv, hashlib

# Mute Deprecation Warnings (TripleDES/Paramiko errors)
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
            "JWT_Token": r'ey[a-zA-Z0-9]{50,}\.ey[a-zA-Z0-9]{50,}\.[a-zA-Z0-9_-]+',
            "Email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "Phone": r'\+?[1-9]\d{1,14}',
            "SQL_Query": r'(SELECT\s+.*\s+FROM\s+.*|INSERT\s+INTO\s+.*|UPDATE\s+.*SET\s+.*)',
            "Sensitive_Path": r'/(?:config|admin|backup|v1|api|debug|env)/[a-zA-Z0-9\._/-]+',
            "URL_Hardcoded": r'https?://[^\s"\'>]+'
        }
        self._prepare_csvs()

    def _prepare_csvs(self):
        files_headers = [
            (KEY_MEGA_CSV, ['Timestamp', 'Type', 'Data', 'Source']),
            (IP_MEGA_CSV, ['Timestamp', 'IP', 'Type', 'Source']),
            (APK_HASH_CSV, ['Package_Name', 'Last_Hash', 'Last_Seen'])
        ]
        for file, headers in files_headers:
            if not os.path.exists(file):
                with open(file, 'w', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow(headers)

    async def pwn_binary_analysis(self, file_path):
        if not PWN_AVAILABLE: return
        try:
            print(f"   🛡️ {B}[PWN-ANALYSIS]{RS} Checking Binary: {os.path.basename(file_path)}")
            context.arch = 'arm' 
            elf = ELF(file_path, checksec=False)
            
            stats = {
                "NX (No-Execute)": elf.nx,
                "Stack Canary": elf.canary,
                "PIE (Position Independent)": elf.pie,
                "RWX Segments": elf.rwx
            }
            
            for k, v in stats.items():
                status = f"{G}Enabled" if v else f"{R}Disabled"
                print(f"      - {k}: {status}{RS}")
                await self.save_key_to_mega("PWN_Check", f"{k}:{v}", file_path)
        except: pass

    async def check_apk_integrity(self, pkg_name, current_hash):
        df = pd.read_csv(APK_HASH_CSV)
        if pkg_name in df['Package_Name'].values:
            old_hash = df[df['Package_Name'] == pkg_name]['Last_Hash'].values[0]
            if old_hash != current_hash:
                print(f"\n {R}[!!!] WARNING: APK INTEGRITY VIOLATION [!!!]{RS}")
                df.loc[df['Package_Name'] == pkg_name, ['Last_Hash', 'Last_Seen']] = [current_hash, datetime.now().isoformat()]
                df.to_csv(APK_HASH_CSV, index=False)
                return False
        else:
            new_data = pd.DataFrame([{'Package_Name': pkg_name, 'Last_Hash': current_hash, 'Last_Seen': datetime.now().isoformat()}])
            new_data.to_csv(APK_HASH_CSV, mode='a', header=False, index=False)
        return True

    async def analyze_apk(self, target_input):
        if target_input in self.downloaded_files: return
        self.downloaded_files.add(target_input)
        
        filename = ""
        is_local = os.path.exists(target_input)

        try:
            if is_local:
                filename = target_input
                print(f"   📂 {G}[LOCAL-FILE]{RS} Processing: {os.path.basename(filename)}")
            else:
                if not target_input.startswith(('http://', 'https://')):
                    print(f" {R}[!] Error: Invalid URL or Path.{RS}")
                    return
                filename = os.path.join(DOWNLOAD_DIR, target_input.split('/')[-1])
                if not filename.endswith('.apk'): filename += ".apk"
                print(f"   📥 {Y}[APK-DOWNLOAD]{RS} Fetching...")
                async with httpx.AsyncClient(verify=False, timeout=60) as client:
                    resp = await client.get(target_input)
                    if resp.status_code == 200:
                        async with aiofiles.open(filename, "wb") as f: await f.write(resp.content)
                    else: return

            with open(filename, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            apk_obj = APK(filename)
            pkg_name = apk_obj.package
            await self.check_apk_integrity(pkg_name, file_hash)

            info = f"App: {apk_obj.get_app_name()} | Pkg: {pkg_name} | Hash: {file_hash}"
            print(f"   📱 {G}[APK-FOUND]{RS} {info}")
            
            perms = apk_obj.get_permissions()
            print(f"   🔐 {P}[PERMISSIONS]{RS} Total: {len(perms)}")
            
            with zipfile.ZipFile(filename, 'r') as z:
                libs = [name for name in z.namelist() if name.endswith('.so')]
                if libs:
                    print(f"   📦 {B}[NATIVE-LIBS]{RS} Found {len(libs)} .so files")
                    sample_lib = os.path.join(DOWNLOAD_DIR, "temp_sample.so")
                    with z.open(libs[0]) as source, open(sample_lib, "wb") as target:
                        target.write(source.read())
                    await self.pwn_binary_analysis(sample_lib)
                    os.remove(sample_lib)

            print(f"   🔗 {C}[EXTRACTING]{RS} Searching for endpoints...")
            await self.deep_file_miner(filename, target_input)
            
            await self.save_key_to_mega("APK_Scan", info, target_input)
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
                        if name.endswith(('.xml', '.json', '.txt')):
                            with z.open(name) as f: text_content += f.read().decode(errors='ignore')
            if text_content:
                for name, pattern in self.patterns.items():
                    matches = re.findall(pattern, text_content)
                    for m in set(matches):
                        await self.save_key_to_mega(f"InFile_{name}", m, url)
        except: pass

    async def subdomain_enumeration(self):
        print(f" {Y}[ENUM]{RS} Hunting subdomains for: {self.domain}")
        try:
            subs = sublist3r.main(self.domain, 40, None, silent=True, verbose=False, engines=None)
            if subs:
                for s in subs: self.queue.put_nowait(f"https://{s}")
        except: pass

    async def network_scan(self):
        print(f" {B}[NET-SCAN]{RS} Probing ports for: {self.domain}")
        try:
            target_ip = socket.gethostbyname(self.domain)
            common_ports = [21, 22, 23, 80, 443, 3306, 8080]
            for port in common_ports:
                try:
                    conn = asyncio.open_connection(target_ip, port)
                    await asyncio.wait_for(conn, timeout=1.0)
                    print(f"   🔥 {G}[PORT-OPEN]{RS} {port}")
                except: continue
        except: pass

    async def worker(self, sem):
        while True:
            url = await self.queue.get()
            if url in self.visited_urls: self.queue.task_done(); continue
            self.visited_urls.add(url)
            async with sem:
                res = await self.fetch_page(url)
                if res and res[0]:
                    links = re.findall(r'(?:href|src|url)=["\'](.*?)["\']', res[0])
                    for link in set(links):
                        if self.domain.split('.')[0] in link: self.queue.put_nowait(urljoin(url, link))
            self.queue.task_done()

    async def start(self):
        print(f"\n{P}⚡ HASSAN AI V110: ULTIMATE EDITION ⚡{RS}")
        await self.subdomain_enumeration()
        self.queue.put_nowait(self.target + "/")
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
    mode = input(f"{C}Select Mode: {RS}").strip().lower()
    
    targets = []

    if mode == 'b':
        path = input(f"{P}Binary File Path: {RS}").strip()
        if os.path.exists(path):
            vault = HassanAI_Vault("local.host")
            await vault.pwn_binary_analysis(path)
        return

    if mode == 'x':
        t = input(f"{G}Target (example.com): {RS}").strip()
        if t: targets.append(t)

    elif mode == 'k':
        t = input(f"{P}APK Path or Link: {RS}").strip().rstrip('/')
        if t:
            vault = HassanAI_Vault(t)
            await vault.analyze_apk(t)
            return

    elif mode == 'm':
        t = input(f"{B}Network Target: {RS}").strip()
        if t:
            vault = HassanAI_Vault(t)
            await vault.network_scan()
            return
            
    for t in targets:
        print(f"\n {C}🚀 Starting Scan for: {t}{RS}")
        vault = HassanAI_Vault(t)
        await vault.start()

if __name__ == "__main__":
    try: asyncio.run(main_controller())
    except KeyboardInterrupt: print(f"\n{R}[!] Stopped.{RS}")
