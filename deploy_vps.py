import paramiko
import os
import time

# Server ma'lumotlari
host = "45.126.124.232"
username = "root"
password = "Muhammadmuso00"

def deploy():
    try:
        print(f"Connecting to {host} as {username}...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password, timeout=30, banner_timeout=30, look_for_keys=False, allow_agent=False)
        
        print("Creating bot directory...")
        client.exec_command("mkdir -p ~/bot")
        
        sftp = client.open_sftp()
        print("Uploading files...")
        
        # Kerakli fayllar va papkalar ro'yxati
        files_to_upload = [
            "bot.py", "database.py", "config.py", "requirements.txt", ".env", "Procfile"
        ]
        folders_to_upload = ["handlers", "keyboards", "middleware"]
        
        # Fayllarni yuklash
        for file in files_to_upload:
            if os.path.exists(file):
                print(f"Uploading {file}...")
                sftp.put(file, f"bot/{file}")
        
        # Papkalarni yuklash
        for folder in folders_to_upload:
            if os.path.exists(folder):
                client.exec_command(f"mkdir -p ~/bot/{folder}")
                for f in os.listdir(folder):
                    local_path = os.path.join(folder, f)
                    if os.path.isfile(local_path):
                        print(f"Uploading {local_path}...")
                        sftp.put(local_path, f"bot/{folder}/{f}")
        
        sftp.close()
        
        print("Installing requirements (this may take a while)...")
        stdin, stdout, stderr = client.exec_command("cd ~/bot && pip3 install --user -r requirements.txt")
        # Chiqishni kutish
        stdout.channel.recv_exit_status()
        
        print("Starting the bot inside screen...")
        # Oldingi screenlarni tozalash (ixtiyoriy)
        client.exec_command("screen -S mybot -X quit")
        # Yangi screen ochib botni ishga tushirish
        client.exec_command("cd ~/bot && screen -dmS mybot python3 bot.py")
        
        print("\nSUCCESS! Bot is now running on your VPS.")
        print("To check logs on VPS, use: screen -r mybot")
        
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    deploy()
