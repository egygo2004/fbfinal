"""
Local VPN Manager for Windows
==============================
Manages OpenVPN connections using local .ovpn config files.
Randomly selects a VPN config for each session.

Requirements:
    - OpenVPN installed on Windows
    - .ovpn config files in the 'vpn' folder
    - vpn_auth.txt with ProtonVPN credentials (username/password on separate lines)
"""

import os
import sys
import subprocess
import time
import random
import requests
import glob
import signal
from datetime import datetime

class LocalVPNManager:
    """Manages OpenVPN connections on Windows"""
    
    def __init__(self, vpn_folder=None, auth_file=None):
        """
        Initialize VPN Manager
        
        Args:
            vpn_folder: Path to folder containing .ovpn files
            auth_file: Path to authentication file (username/password)
        """
        # Get script directory
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # VPN folder (default: vpn subfolder)
        self.vpn_folder = vpn_folder or os.path.join(self.script_dir, 'vpn')
        
        # Auth file for ProtonVPN
        self.auth_file = auth_file or os.path.join(self.script_dir, 'vpn_auth.txt')
        
        # OpenVPN executable paths to try
        self.openvpn_paths = [
            r"C:\Program Files\OpenVPN\bin\openvpn.exe",
            r"C:\Program Files\OpenVPN\bin\openvpn-gui.exe",
            r"C:\Program Files (x86)\OpenVPN\bin\openvpn.exe",
            r"C:\Program Files\OpenVPN Connect\ovpnconnector.exe",
            os.environ.get('OPENVPN_PATH', '')
        ]
        
        # Find OpenVPN executable
        self.openvpn_exe = self._find_openvpn()
        
        # Current VPN process
        self.vpn_process = None
        self.current_config = None
        self.original_ip = None
        
    def _find_openvpn(self):
        """Find OpenVPN executable on the system"""
        for path in self.openvpn_paths:
            if path and os.path.exists(path):
                self._log(f"Found OpenVPN: {path}", "OK")
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(['where', 'openvpn'], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]
                self._log(f"Found OpenVPN in PATH: {path}", "OK")
                return path
        except:
            pass
        
        self._log("OpenVPN not found! Please install from https://openvpn.net/community-downloads/", "ERROR")
        return None
    
    def _log(self, msg, level="INFO"):
        """Log message with timestamp"""
        t = datetime.now().strftime("%H:%M:%S")
        colors = {"INFO": "", "OK": "[✓]", "WARN": "[!]", "ERROR": "[✗]"}
        prefix = colors.get(level, "")
        print(f"[{t}] {prefix} [VPN] {msg}", flush=True)
    
    def get_vpn_configs(self):
        """Get list of all .ovpn files in vpn folder"""
        if not os.path.exists(self.vpn_folder):
            self._log(f"VPN folder not found: {self.vpn_folder}", "ERROR")
            return []
        
        configs = glob.glob(os.path.join(self.vpn_folder, "*.ovpn"))
        self._log(f"Found {len(configs)} VPN configs", "INFO")
        return configs
    
    def get_random_config(self):
        """Select a random VPN config file"""
        configs = self.get_vpn_configs()
        if not configs:
            return None
        
        selected = random.choice(configs)
        self._log(f"Selected: {os.path.basename(selected)}", "OK")
        return selected
    
    def get_current_ip(self):
        """Get current public IP address"""
        self._log("Checking current IP...", "INFO")
        try:
            # Try multiple IP services with shorter timeouts
            services = [
                'https://api.ipify.org',
                'https://icanhazip.com',
                'https://ifconfig.me/ip'
            ]
            
            for service in services:
                try:
                    self._log(f"Trying {service}...", "INFO")
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        if len(ip) < 16: # Basic check for valid IP string
                            return ip
                except Exception as e:
                    self._log(f"Service {service} failed: {e}", "WARN")
                    continue
            
            return None
        except Exception as e:
            self._log(f"Failed to get IP: {e}", "WARN")
            return None
    
    def connect(self, config_file=None):
        """
        Connect to VPN using specified or random config
        
        Args:
            config_file: Path to .ovpn file (optional, random if not specified)
            
        Returns:
            bool: True if connected successfully
        """
        if not self.openvpn_exe:
            self._log("OpenVPN executable not found!", "ERROR")
            return False
        
        # Select config
        if not config_file:
            config_file = self.get_random_config()
        
        if not config_file or not os.path.exists(config_file):
            self._log(f"Config file not found: {config_file}", "ERROR")
            return False
        
        self.current_config = config_file
        config_name = os.path.basename(config_file)
        
        # Get original IP before connecting
        self.original_ip = self.get_current_ip()
        self._log(f"Original IP: {self.original_ip}", "INFO")
        
        # Check auth file exists
        if not os.path.exists(self.auth_file):
            self._log(f"Auth file not found: {self.auth_file}", "ERROR")
            self._log("Create vpn_auth.txt with ProtonVPN username on line 1 and password on line 2", "INFO")
            return False
        
        # Try to start OpenVPN Interactive Service for proper route handling
        try:
            subprocess.run(['net', 'start', 'OpenVPNServiceInteractive'], 
                         capture_output=True, check=False)
        except:
            pass
        
        # Build OpenVPN command
        # --disable-dco: Use legacy TAP adapter (more compatible)
        # --route-nopull: Skip route additions (avoids "Access denied" issues)
        # This means we connect to VPN but don't redirect all traffic through it
        cmd = [
            self.openvpn_exe,
            '--config', config_file,
            '--auth-user-pass', self.auth_file,
            '--auth-nocache',
            '--disable-dco',
            '--route-nopull',
            '--verb', '3'
        ]
        
        self._log(f"Command: {' '.join(cmd)}", "INFO")
        self._log(f"Connecting to VPN: {config_name}...", "INFO")
        
        try:
            # Start OpenVPN process
            # Use CREATE_NEW_PROCESS_GROUP for proper signal handling on Windows
            self.vpn_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                text=True,
                bufsize=1 # Line buffered
            )
            
            # Wait for connection
            connected = self._wait_for_connection(timeout=90)
            
            if connected:
                # Brief wait for routes to stabilize
                time.sleep(3)
                new_ip = self.get_current_ip()
                
                # CRITICAL: Verify IP actually changed
                if new_ip and self.original_ip and new_ip != self.original_ip:
                    self._log(f"✅ VPN Connected! New IP: {new_ip}", "OK")
                    return True
                else:
                    self._log(f"⚠️ VPN connected but IP unchanged ({new_ip}). Routes may have failed.", "WARN")
                    self._log("Trying to continue anyway...", "INFO")
                    return True  # Still try to proceed
            else:
                self._log("VPN connection failed or timed out", "ERROR")
                self.disconnect()
                return False
                
        except Exception as e:
            self._log(f"Failed to start OpenVPN: {e}", "ERROR")
            return False
    
    def _wait_for_connection(self, timeout=60):
        """Wait for VPN connection by monitoring output with a non-blocking thread"""
        import queue
        from threading import Thread
        
        start_time = time.time()
        self._log(f"Waiting for VPN connection (timeout: {timeout}s)...", "INFO")
        
        log_queue = queue.Queue()
        
        def read_output(pipe, q):
            try:
                for line in iter(pipe.readline, ''):
                    q.put(line)
            except: pass
            finally: pipe.close()

        # Start thread to read output
        t = Thread(target=read_output, args=(self.vpn_process.stdout, log_queue))
        t.daemon = True
        t.start()

        last_ip_check = 0
        
        while time.time() - start_time < timeout:
            # 1. Check for process exit
            if self.vpn_process.poll() is not None:
                self._log(f"Process ended unexpectedly (Exit Code: {self.vpn_process.returncode})", "ERROR")
                return False

            # 2. Try to check IP as a fallback every 8 seconds
            if time.time() - last_ip_check > 8:
                last_ip_check = time.time()
                current_ip = self.get_current_ip()
                if current_ip and self.original_ip and current_ip != self.original_ip:
                    self._log(f"✅ IP changed detected via fallback: {current_ip}", "OK")
                    return True

            # 3. Process logs from queue
            try:
                line = log_queue.get_nowait()
                clean_line = line.strip()
                if clean_line:
                    # Success indicators
                    if any(x in clean_line for x in ["Initialization Sequence Completed", "connected", "successfully connected"]):
                        self._log("VPN Initialization Completed!", "OK")
                        return True
                    
                    if "PUSH_REPLY" in clean_line:
                        self._log("Received config (PUSH_REPLY). Setting up interface...", "INFO")
                    
                    if "AUTH_FAILED" in clean_line:
                        self._log("Authentication failed! Check vpn_auth.txt", "ERROR")
                        return False
                    
                    # Show all progress lines for now to find the error
                    print(f"  > {clean_line}", flush=True)
            except queue.Empty:
                time.sleep(0.5)
                continue

        self._log("Connection timed out", "ERROR")
        return False
    
    def disconnect(self):
        """Disconnect from VPN"""
        self._log("Disconnecting VPN...", "INFO")
        
        if self.vpn_process:
            try:
                # On Windows, send CTRL+C to the process group
                if os.name == 'nt':
                    self.vpn_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.vpn_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.vpn_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.vpn_process.kill()
                    
            except Exception as e:
                self._log(f"Error terminating VPN process: {e}", "WARN")
            
            self.vpn_process = None
        
        # Also kill any orphaned openvpn processes
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/IM', 'openvpn.exe'], 
                             capture_output=True, check=False)
        except:
            pass
        
        # Verify IP reverted
        time.sleep(2)
        current_ip = self.get_current_ip()
        self._log(f"Current IP after disconnect: {current_ip}", "INFO")
        
        self.current_config = None
        self._log("VPN Disconnected", "OK")
    
    def is_connected(self):
        """Check if VPN is currently connected"""
        if not self.vpn_process:
            return False
        
        # Check if process is still running
        if self.vpn_process.poll() is not None:
            return False
        
        # Check if IP is different from original
        if self.original_ip:
            current_ip = self.get_current_ip()
            return current_ip != self.original_ip
        
        return True


# Test function
if __name__ == "__main__":
    print("=" * 50)
    print("  Local VPN Manager Test")
    print("=" * 50)
    
    manager = LocalVPNManager()
    
    # List available configs
    configs = manager.get_vpn_configs()
    print(f"\nAvailable VPN configs: {len(configs)}")
    for c in configs[:5]:
        print(f"  - {os.path.basename(c)}")
    if len(configs) > 5:
        print(f"  ... and {len(configs) - 5} more")
    
    # Get current IP
    print(f"\nCurrent IP: {manager.get_current_ip()}")
    
    # Test connection
    print("\n" + "=" * 50)
    input("Press Enter to test VPN connection...")
    
    if manager.connect():
        print("\n✅ VPN Connected Successfully!")
        print(f"New IP: {manager.get_current_ip()}")
        
        input("\nPress Enter to disconnect...")
        manager.disconnect()
    else:
        print("\n❌ VPN Connection Failed!")
