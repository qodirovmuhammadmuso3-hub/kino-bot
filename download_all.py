import paramiko
import os
import stat

def download_dir(sftp, remote_dir, local_dir):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
        print(f"Created local directory: {local_dir}")
        
    for entry in sftp.listdir_attr(remote_dir):
        remote_path = os.path.join(remote_dir, entry.filename).replace('\\', '/')
        local_path = os.path.join(local_dir, entry.filename)
        
        mode = entry.st_mode
        if stat.S_ISDIR(mode):
            # It's a directory, recursion
            download_dir(sftp, remote_path, local_path)
        elif stat.S_ISREG(mode):
            # It's a file, download
            print(f"Downloading: {remote_path} -> {local_path}")
            sftp.get(remote_path, local_path)

def main():
    host = '104.248.140.99'
    user = 'root'
    password = r'(M20072007m'
    remote_root = '/root/kino-bot'
    local_root = r'c:\Users\MUhammadmuso\Desktop\kino bot'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host}...")
        ssh.connect(host, username=user, password=password, timeout=10)
        sftp = ssh.open_sftp()
        
        print(f"Starting recursive download from {remote_root}...")
        download_dir(sftp, remote_root, local_root)
        
        print("\nDownload complete!")
        sftp.close()
    except Exception as e:
        print(f"Error during download: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
