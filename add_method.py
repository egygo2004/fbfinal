with open('fb_otp_browser_new.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "def run_flow(self, phone):"
for i, line in enumerate(lines):
    if '    def run_flow(self, phone):' in line:
        # Insert run_flow_reuse before it
        insert_lines = [
            '\n',
            '    def run_flow_reuse(self, phone):\n',
            '        """Reuse existing browser (for persistent mode)"""\n',
            '        return self.run_flow(phone)\n',
            '\n'
        ]
        lines = lines[:i] + insert_lines + lines[i:]
        break

with open('fb_otp_browser.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done! Added run_flow_reuse to fb_otp_browser.py")
