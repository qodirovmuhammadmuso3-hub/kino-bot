import paramiko
import os

def read_remote_file(file_path):
    host = '104.248.140.99'
    user = 'root'
    password = r'(M20072007m'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(f'cat {file_path}')
        content = stdout.read().decode()
        return content
    except Exception as e:
        return f"Error: {e}"
    finally:
        ssh.close()

if __name__ == '__main__':
    # Reading main.py
    main_content = read_remote_file('/root/kino-bot/main.py')
    print("--- START OF main.py ---")
    print(main_content)
    print("--- END OF main.py ---")
    
    # Reading handlers/admin.py
    admin_content = read_remote_file('/root/kino-bot/handlers/admin.py')
    print("--- START OF handlers/admin.py ---")
    # print(admin_content) # Maybe too long, just check if it exists
    print(f"Read {len(admin_content)} characters from handlers/admin.py")
