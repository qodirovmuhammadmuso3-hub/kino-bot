import paramiko
import time

def run_cmd(ssh, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    
    if out:
        print("STDOUT:", out)
    if err:
        print("STDERR:", err)
    
    print(f"Exit status: {exit_status}\n")
    return out, err, exit_status

def main():
    host = '104.248.140.99'
    user = 'root'
    password = 'M20072007'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Connecting to server...")
        ssh.connect(host, username=user, password=password, timeout=10)
        print("Connected successfully!")
        
        # Checking where the bot is located
        out, _, _ = run_cmd(ssh, "find /root -name 'main.py' -o -name 'bot.py'")
        
        # We assume they want it in /root/kino-bot
        # Let's clone or pull
        repo_url = "https://github.com/qodirovmuhammadmuso3-hub/kino-bot.git"
        
        setup_script = f"""
        if [ ! -d "/root/kino-bot" ]; then
            cd /root && git clone {repo_url}
        fi
        cd /root/kino-bot
        git config --global pull.rebase false
        git reset --hard HEAD
        git pull origin main
        
        # Install requirements
        python3 -m venv venv || true
        source venv/bin/activate || true
        pip install -r requirements.txt
        
        echo 'Deployment script finished syncing code.'
        """
        
        run_cmd(ssh, setup_script)
        
        # Optional: finding active systemd service
        out, _, _ = run_cmd(ssh, "systemctl list-units --type=service | grep kino")
        
    except Exception as e:
        print("Error:", e)
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
