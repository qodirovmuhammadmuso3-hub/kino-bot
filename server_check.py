import paramiko
import os

def list_server_files():
    host = '104.248.140.99'
    user = 'root'
    password = r'(M20072007m'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host}...")
        ssh.connect(host, username=user, password=password, timeout=10)
        print("Connected successfully!")
        
        # Look for the bot directory
        stdin, stdout, stderr = ssh.exec_command('ls -F /root')
        print("Files in /root:")
        print(stdout.read().decode())
        
        # Check /root/kino-bot
        ssh.exec_command('cd /root/kino-bot && ls -R')
        stdin, stdout, stderr = ssh.exec_command('ls -R /root/kino-bot')
        print("\nFiles in /root/kino-bot:")
        print(stdout.read().decode())
        
        # Also check for .env to see what's what
        stdin, stdout, stderr = ssh.exec_command('cat /root/kino-bot/.env')
        print("\nContent of .env on server:")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Failed: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    list_server_files()
