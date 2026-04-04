import paramiko
import os

def list_server_files():
    host = '104.248.140.99'
    user = 'root'
    passwords = ['(M20072007', 'M20072007']
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for password in passwords:
        try:
            print(f"Trying password: {password}")
            ssh.connect(host, username=user, password=password, timeout=10)
            print("Connected!")
            stdin, stdout, stderr = ssh.exec_command('find /root/kino-bot -maxdepth 2')
            print(stdout.read().decode())
            return
        except Exception as e:
            print(f"Failed with {password}: {e}")
        finally:
            ssh.close()

if __name__ == '__main__':
    list_server_files()
