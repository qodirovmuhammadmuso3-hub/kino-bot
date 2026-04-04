import paramiko

def test_connection():
    host = '104.248.140.99'
    user = 'root'
    password = '(M20072007'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Testing connection...")
        ssh.connect(host, username=user, password=password, timeout=10)
        print("Success! Logged in as root.")
        stdin, stdout, stderr = ssh.exec_command('pwd')
        print(stdout.read().decode())
    except Exception as e:
        print("Failed:", e)
    finally:
        ssh.close()

if __name__ == '__main__':
    test_connection()
